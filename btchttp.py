from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urlparse
import time
import os.path
import simplejson
import socket

try:
	import bitcoinrpc.authproxy
except ImportError:
	print "Error: Please install bitcoinrpc: https://github.com/jgarzik/python-bitcoinrpc"

PORT = 8154
BITCOINRPC = 'http://john_oliver:KGbv6HvJ5z@127.0.0.1:8332/'

GETBLOCK = "/rest/block"
GETTX = "/rest/tx"

FORMATS = {"binary" : "application/octet-stream", "hex" : "text/plain", "json" : "application/json"}
DEFAULT_FORMAT = "json"

#sample URLs:
#	http://localhost:8154/rest/block/00000000000000183d1cb83091e0140c32604ab206cd0d531f90f24d7d329374
#	http://localhost:8154/rest/tx/da4e993438a1a0bb75cbb02db99876f263737a68ff4ad762eb949ad72e23ae6c?format=binary

class MyHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		print("%s: Just received a GET request" % time.ctime())

		qs = {}
		path = self.path
		if '?' in path:
			path, tmp = path.split('?', 1)
			qs = urlparse.parse_qs(tmp)
		print path, qs

		if "format" in qs:
			format = qs["format"][0]
		else:
			format = DEFAULT_FORMAT

		if os.path.dirname(path) == GETBLOCK:
			self.get_block(os.path.basename(path), format)
		elif os.path.dirname(path) == GETTX:
			self.get_tx(os.path.basename(path), format)
		else:
			self.send_headers(400)
			self.wfile.write("Unknown request")

		return

	def send_headers(self, code, accept_type):
		self.send_response(code)
		self.send_header("Accept", FORMATS[accept_type])
		self.end_headers()

	def get_block(self, blockhash, format):
		print "Getting block %s" % (blockhash)
		#print "Getting block %s (encoding: %s)" % (blockhash, format)

		try:
			block_info = self.server.btcrpc.getblock(blockhash)
			msg = simplejson.dumps(block_info, use_decimal=True)
			code = 200
		except socket.error as msg:
			msg = "Error connecting to bitcoind: %s" % msg
			code = 404
		except bitcoinrpc.authproxy.JSONRPCException:
			msg = "bitcoind returned an error! Have you specified a valid block hash?"
			code = 404

		self.send_headers(code, format)
		self.wfile.write(msg)

	def get_tx(self, txid, format):
		print "Getting transaction %s (encoding: %s)" % (txid, format)

		try:
			tx_info = self.server.btcrpc.getrawtransaction(txid, 1)
			if format == "json":
				msg = simplejson.dumps(tx_info, use_decimal=True)
			elif format == "hex":
				msg = tx_info['hex']
			elif format == "binary":
				msg = tx_info['hex'].decode('hex')
			code = 200
		except socket.error as msg:
			msg = "Error connecting to bitcoind: %s" % msg
			code = 404
		except bitcoinrpc.authproxy.JSONRPCException:
			msg = "bitcoind returned an error! Have you specified a valid transaction id, and do you have txindex=1 specified in bitcoin.conf?"
			code = 404

		self.send_headers(code, format)
		self.wfile.write(msg)

if __name__ == "__main__":
	try:
		server = HTTPServer(('0.0.0.0', PORT), MyHandler)
		#server.socket = ssl.wrap_socket(server.socket, certfile='server.pem', server_side=True)
		btcrpc = bitcoinrpc.authproxy.AuthServiceProxy(BITCOINRPC)
		server.btcrpc = btcrpc
		print('Started http server at port %d' % PORT)
		server.serve_forever()
	except KeyboardInterrupt:
		print('^C received, shutting down server')
		server.socket.close()
