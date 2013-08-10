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

class MyHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		print("%s: Just received a GET request" % time.ctime())

		path = self.path

		if os.path.dirname(path) == GETBLOCK:
			self.get_block(os.path.basename(path))
		elif os.path.dirname(path) == GETTX:
			self.get_tx(os.path.basename(path))
		else:
			self.send_headers(400)
			self.wfile.write("Unknown request")

		return

	def send_headers(self, code):
		self.send_response(code)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def get_block(self, blockhash):
		print "Getting block %s" % blockhash

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

		self.send_headers(code)
		self.wfile.write(msg)

	def get_tx(self, txid):
		print "Getting transaction %s" % txid

		try:
			tx_info = self.server.btcrpc.getrawtransaction(txid, 1)
			msg = simplejson.dumps(tx_info, use_decimal=True)
			code = 200
		except socket.error as msg:
			msg = "Error connecting to bitcoind: %s" % msg
			code = 404
		except bitcoinrpc.authproxy.JSONRPCException:
			msg = "bitcoind returned an error! Have you specified a valid transaction id, and do you have txindex=1 specified in bitcoin.conf?"
			code = 404

		self.send_headers(code)
		self.wfile.write(msg)

if __name__ == "__main__":
	try:
		server = HTTPServer(('0.0.0.0', PORT), MyHandler)
		btcrpc = bitcoinrpc.authproxy.AuthServiceProxy(BITCOINRPC)
		server.btcrpc = btcrpc
		print('Started http server at port %d' % PORT)
		server.serve_forever()
	except KeyboardInterrupt:
		print('^C received, shutting down server')
		server.socket.close()
