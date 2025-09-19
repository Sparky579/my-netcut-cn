import os
import sqlite3
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS

UPLOAD_DIR = Path(__file__).parent / 'uploads'
DB_PATH = Path(__file__).parent / 'app.db'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

APP_PORT = 23456

# 数据库辅助

def get_db():
	if 'db' not in g:
		g.db = sqlite3.connect(DB_PATH)
		g.db.row_factory = sqlite3.Row
	return g.db


def close_db(e=None):
	db = g.pop('db', None)
	if db is not None:
		db.close()


def init_db():
	db = get_db()
	db.executescript(
		'''
		CREATE TABLE IF NOT EXISTS app_keys (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			key TEXT NOT NULL UNIQUE,
			created_at INTEGER NOT NULL
		);

		CREATE TABLE IF NOT EXISTS channels (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL UNIQUE,
			content TEXT,
			password_hash TEXT,
			expire_at INTEGER,
			owner_key TEXT,
			FOREIGN KEY(owner_key) REFERENCES app_keys(key)
		);

		CREATE TABLE IF NOT EXISTS files (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			channel_name TEXT NOT NULL,
			stored_name TEXT NOT NULL,
			original_name TEXT NOT NULL,
			size INTEGER NOT NULL,
			uploaded_at INTEGER NOT NULL,
			expire_at INTEGER,
			FOREIGN KEY(channel_name) REFERENCES channels(name)
		);
		'''
	)
	# 迁移：为 app_keys 增加 expires_at 列
	cols = [r['name'] for r in db.execute("PRAGMA table_info('app_keys')").fetchall()]
	if 'expires_at' not in cols:
		db.execute('ALTER TABLE app_keys ADD COLUMN expires_at INTEGER')
	db.commit()


def now_ts() -> int:
	return int(time.time())


def hash_password(password: str) -> str:
	return hashlib.sha256(password.encode('utf-8')).hexdigest()


def require_master_key(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		data = request.headers.get('x-master-key') or request.args.get('master_key')
		if not data:
			return jsonify({'error': 'missing_master_key'}), 401
		db = get_db()
		row = db.execute('SELECT key, created_at, expires_at FROM app_keys WHERE key = ?', (data,)).fetchone()
		if not row:
			return jsonify({'error': 'invalid_master_key'}), 401
		if row['expires_at'] is not None and row['expires_at'] > 0 and row['expires_at'] < now_ts():
			return jsonify({'error': 'expired_master_key'}), 401
		# 将当前密钥信息放到 g 中以便后续使用
		g.current_key = row
		return func(*args, **kwargs)
	return wrapper


def require_channel_access(func):
	@wraps(func)
	def wrapper(channel: str, *args, **kwargs):
		# 校验主密钥
		mk = request.headers.get('x-master-key') or request.args.get('master_key')
		db = get_db()
		row = db.execute('SELECT key, expires_at FROM app_keys WHERE key = ?', (mk,)).fetchone()
		if not row:
			return jsonify({'error': 'invalid_master_key'}), 401
		if row['expires_at'] is not None and row['expires_at'] > 0 and row['expires_at'] < now_ts():
			return jsonify({'error': 'expired_master_key'}), 401

		# 校验频道密码（若设置）
		pwd = request.headers.get('x-channel-password') or (request.json.get('password') if request.is_json else None) or request.args.get('password')
		info = db.execute('SELECT password_hash, expire_at FROM channels WHERE name = ?', (channel,)).fetchone()
		if info is not None:
			if info['expire_at'] is not None and info['expire_at'] > 0 and info['expire_at'] < now_ts():
				# 过期，执行清理
				cleanup_channel(channel)
				return jsonify({'error': 'channel_expired'}), 410
			ph = info['password_hash']
			if ph and (not pwd or hash_password(pwd) != ph):
				return jsonify({'error': 'password_required'}), 403
		return func(channel, *args, **kwargs)
	return wrapper


def cleanup_channel(channel_name: str):
	db = get_db()
	files = db.execute('SELECT stored_name FROM files WHERE channel_name = ?', (channel_name,)).fetchall()
	for f in files:
		p = UPLOAD_DIR / f['stored_name']
		if p.exists():
			try:
				p.unlink()
			except Exception:
				pass
	db.execute('DELETE FROM files WHERE channel_name = ?', (channel_name,))
	db.execute('DELETE FROM channels WHERE name = ?', (channel_name,))
	db.commit()


def periodic_cleanup():
	db = get_db()
	# 清理过期文件
	expired_files = db.execute('SELECT id, stored_name FROM files WHERE expire_at IS NOT NULL AND expire_at > 0 AND expire_at < ?', (now_ts(),)).fetchall()
	for f in expired_files:
		p = UPLOAD_DIR / f['stored_name']
		if p.exists():
			try:
				p.unlink()
			except Exception:
				pass
		db.execute('DELETE FROM files WHERE id = ?', (f['id'],))
	# 清理过期频道
	expired_channels = db.execute('SELECT name FROM channels WHERE expire_at IS NOT NULL AND expire_at > 0 AND expire_at < ?', (now_ts(),)).fetchall()
	for c in expired_channels:
		cleanup_channel(c['name'])
	db.commit()


def create_app() -> Flask:
	app = Flask(__name__)
	CORS(app, supports_credentials=True)
	app.teardown_appcontext(close_db)

	with app.app_context():
		init_db()
		# 初始化主密钥（仅首次），为永久密钥（expires_at 为空）
		db = get_db()
		row = db.execute('SELECT key FROM app_keys LIMIT 1').fetchone()
		if not row:
			mk = secrets.token_urlsafe(24)
			db.execute('INSERT INTO app_keys(key, created_at, expires_at) VALUES(?, ?, ?)', (mk, now_ts(), None))
			db.commit()
			print('First master key generated (display once):', mk)

	@app.get('/api/health')
	def health():
		return jsonify({'ok': True})

	@app.get('/api/master/exists')
	def master_exists():
		db = get_db()
		row = db.execute('SELECT key FROM app_keys LIMIT 1').fetchone()
		return jsonify({'exists': row is not None})

	@app.post('/api/master/peek-once')
	def master_peek_once():
		# 仅在首次没有前端密钥时调用，用于显示一次
		db = get_db()
		row = db.execute('SELECT key FROM app_keys LIMIT 1').fetchone()
		if not row:
			return jsonify({'error': 'not_initialized'}), 500
		return jsonify({'master_key': row['key']})

	@app.get('/api/master/me')
	@require_master_key
	def master_me():
		row = g.current_key
		is_permanent = row['expires_at'] is None
		return jsonify({
			'created_at': row['created_at'],
			'expires_at': row['expires_at'],
			'is_permanent': is_permanent,
			'can_rotate': bool(is_permanent),
		})

	@app.post('/api/master/rotate')
	@require_master_key
	def master_rotate():
		# 仅永久密钥可生成新密钥；支持 minutes: 60/1440/10080
		parent = g.current_key
		if parent['expires_at'] is not None:
			return jsonify({'error': 'visitor_cannot_rotate'}), 403
		data = request.get_json(silent=True) or {}
		minutes = data.get('minutes')
		allowed = {60, 1440, 10080}
		if minutes not in allowed:
			return jsonify({'error': 'minutes_invalid', 'allowed': sorted(list(allowed))}), 400
		mk = secrets.token_urlsafe(24)
		exp = now_ts() + int(minutes) * 60
		db = get_db()
		db.execute('INSERT INTO app_keys(key, created_at, expires_at) VALUES(?, ?, ?)', (mk, now_ts(), exp))
		db.commit()
		return jsonify({'master_key': mk, 'expires_at': exp})

	@app.get('/api/channel/<channel>')
	@require_channel_access
	def api_get_channel(channel: str):
		db = get_db()
		row = db.execute('SELECT name, content, expire_at, password_hash FROM channels WHERE name = ?', (channel,)).fetchone()
		if not row:
			return jsonify({'name': channel, 'content': '', 'expire_at': None, 'password_set': False})
		return jsonify({'name': row['name'], 'content': row['content'] or '', 'expire_at': row['expire_at'], 'password_set': bool(row['password_hash'])})

	@app.post('/api/channel/<channel>/save')
	@require_channel_access
	def api_save_channel(channel: str):
		data = request.get_json(force=True)
		content = data.get('content', '')
		expire_minutes = int(data.get('expire_minutes', 10))
		password = data.get('password')
		expire_at = now_ts() + expire_minutes * 60 if expire_minutes > 0 else None

		db = get_db()
		row = db.execute('SELECT name FROM channels WHERE name = ?', (channel,)).fetchone()
		password_hash_val = hash_password(password) if password else None
		if row:
			db.execute('UPDATE channels SET content = ?, expire_at = ?, password_hash = COALESCE(?, password_hash) WHERE name = ?', (content, expire_at, password_hash_val, channel))
		else:
			db.execute('INSERT INTO channels(name, content, expire_at, password_hash) VALUES(?, ?, ?, ?)', (channel, content, expire_at, password_hash_val))
		db.commit()
		return jsonify({'ok': True, 'expire_at': expire_at})

	@app.post('/api/channel/<channel>/password')
	@require_channel_access
	def api_set_channel_password(channel: str):
		data = request.get_json(force=True)
		password = data.get('password')
		db = get_db()
		if not password:
			db.execute('UPDATE channels SET password_hash = NULL WHERE name = ?', (channel,))
		else:
			db.execute('UPDATE channels SET password_hash = ? WHERE name = ?', (hash_password(password), channel))
		db.commit()
		return jsonify({'ok': True})

	@app.post('/api/channel/<channel>/upload')
	@require_channel_access
	def api_upload_file(channel: str):
		if 'file' not in request.files:
			return jsonify({'error': 'no_file'}), 400
		f = request.files['file']
		stored_name = f"{channel}_{secrets.token_hex(8)}_{int(time.time())}"
		path = UPLOAD_DIR / stored_name
		f.save(path)

		expire_minutes = int(request.form.get('expire_minutes', '10'))
		expire_at = now_ts() + expire_minutes * 60 if expire_minutes > 0 else None

		db = get_db()
		db.execute(
			'INSERT INTO files(channel_name, stored_name, original_name, size, uploaded_at, expire_at) VALUES(?,?,?,?,?,?)',
			(channel, stored_name, f.filename or 'file', path.stat().st_size, now_ts(), expire_at)
		)
		db.commit()
		return jsonify({'ok': True})

	@app.get('/api/channel/<channel>/files')
	@require_channel_access
	def api_list_files(channel: str):
		db = get_db()
		rows = db.execute('SELECT id, original_name, size, uploaded_at, expire_at FROM files WHERE channel_name = ? ORDER BY uploaded_at DESC', (channel,)).fetchall()
		files = [dict(id=r['id'], name=r['original_name'], size=r['size'], uploaded_at=r['uploaded_at'], expire_at=r['expire_at']) for r in rows]
		return jsonify({'files': files})

	@app.get('/api/channel/<channel>/download/<int:file_id>')
	@require_channel_access
	def api_download_file(channel: str, file_id: int):
		db = get_db()
		row = db.execute('SELECT stored_name, original_name, expire_at FROM files WHERE id = ? AND channel_name = ?', (file_id, channel)).fetchone()
		if not row:
			return jsonify({'error': 'not_found'}), 404
		if row['expire_at'] is not None and row['expire_at'] > 0 and row['expire_at'] < now_ts():
			return jsonify({'error': 'file_expired'}), 410
		return send_from_directory(UPLOAD_DIR, row['stored_name'], as_attachment=True, download_name=row['original_name'])

	@app.delete('/api/channel/<channel>/file/<int:file_id>')
	@require_channel_access
	def api_delete_file(channel: str, file_id: int):
		db = get_db()
		row = db.execute('SELECT stored_name FROM files WHERE id = ? AND channel_name = ?', (file_id, channel)).fetchone()
		if not row:
			return jsonify({'error': 'not_found'}), 404
		path = UPLOAD_DIR / row['stored_name']
		if path.exists():
			try:
				path.unlink()
			except Exception:
				pass
		db.execute('DELETE FROM files WHERE id = ?', (file_id,))
		db.commit()
		return jsonify({'ok': True})

	@app.get('/api/dashboard')
	def dashboard():
		# 每次访问仪表盘先做一次过期清理
		periodic_cleanup()
		db = get_db()
		# 列出包含文件的频道与大小
		rows = db.execute('SELECT channel_name, SUM(size) AS total FROM files GROUP BY channel_name').fetchall()
		channels = []
		grand = 0
		for r in rows:
			channels.append({'channel': r['channel_name'], 'total': int(r['total'] or 0)})
			grand += int(r['total'] or 0)
		response = jsonify({'channels': channels, 'total_size': grand})
		response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
		response.headers['Pragma'] = 'no-cache'
		response.headers['Expires'] = '0'
		return response

	@app.post('/api/cleanup')
	@require_master_key
	def manual_cleanup():
		periodic_cleanup()
		return jsonify({'ok': True})

	return app


app = create_app()

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=APP_PORT, threaded=True)
