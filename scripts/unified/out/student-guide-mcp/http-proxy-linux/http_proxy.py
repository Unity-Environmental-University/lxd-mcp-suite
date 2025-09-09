import os, json, subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
MAX = int(os.environ.get('MAX_CONTENT_LENGTH', '1048576'))
app.config['MAX_CONTENT_LENGTH'] = MAX
TOKEN = os.environ.get('TOKEN','')
CMD = os.environ.get('SERVER_CMD', '/Users/hallie/Documents/repos/tools/lisa_brain/../student-guide-mcp/mcp_server.py')
CWD = os.environ.get('SERVER_CWD', '/Users/hallie/Documents/repos/tools/lisa_brain/../student-guide-mcp')

@app.post('/call')
def call():
    if TOKEN and request.headers.get('Authorization','') != ('Bearer ' + TOKEN):
        return jsonify({'error':'unauthorized'}), 401
    try:
        req = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({'error':'invalid json'}), 400
    p = subprocess.Popen(['bash','-lc', CMD], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=CWD)
    p.stdin.write(json.dumps(req)+'
'); p.stdin.flush(); p.stdin.close()
    line = p.stdout.readline().strip()
    p.terminate()
    return app.response_class(line, mimetype='application/json')

@app.get('/healthz')
def h(): return jsonify({'status':'ok'})
