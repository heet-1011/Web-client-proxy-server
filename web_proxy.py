from socket import *				#import socket to creat tcp sockets
import threading					#import threading to create all connections on different threads
import time							#import time to get time 
from time import gmtime, strftime	
import queue						#import queue for message passing between different threads

#function that deal with proxy - server communication
def server_communication_handler(http_get_request,server_address,server_port,responsequeue):

	#creating socket for proxy-server communication
	try:
		csocket = socket(AF_INET, SOCK_STREAM)
	except error as e:
		print(f"Socket creation failure: {e}")
	
	#connecting socket with server
	try:
		csocket.connect((server_address, server_port))
	except error as e:
		print(f"Socket connection failure: {e}")
		
	#sending http request to server
	try:
		csocket.send(http_get_request.encode())
		
		#getting http response from server
		http_get_response = b""
		while True:
			upcoming_data = csocket.recv(1024)
			if not upcoming_data:
				break
			http_get_response += upcoming_data
			
		#spliting response
		response_breakdown = http_get_response.split(b"\r\n")
		
		#getting protocol, response_code, response_msg from 1st line of response
		protocol, response_code, response_msg = response_breakdown[0].split(b' ',2)
		
		#dealing as per the response code
		if(response_code == b'200'):
			print("Response Code 200 OK")
		elif(response_code == b'404'):
			print("Error 404 Not Found")
		elif(response_code == b'304'):
			print("Response Code 304 Not Modified")
		elif(response_code == b'301'):
			print("Response Code 301 Moved Permanently")
		
		#storing response in queue so that client side queue can access it
		responsequeue.put(http_get_response)
	except error as e:
		print(f"Request send / Response receive failure: {e}")
	try:
		csocket.close()
	except error as e:
		print("Socket closing error: {e}")
		
#function that deal with client - proxy communication
def client_communication_handler(connection,address):
	print("Client connection with address : ",connection)
	
	#receiving request from the client
	try:
		request = connection.recv(1024)
		request = request.decode()
		print(request)
		
		#request parsing using split
		request_breakdown = request.split("\r\n")
		
		#getting request_method, file_path and protocol from the 1st line of request
		request_method, file_path, protocol = request_breakdown[0].split(' ',2)
		print(file_path)
		
		#splitting headers and storing them into dictionary by converting it into key value pair on further splitting
		headers = {}
		for i in request_breakdown[1:]:
			if i:
				header_name, header_value = i.split(": ")
				headers[header_name] = header_value
		
		#dealing with get request
		if(request_method == "GET"):
			modified_time = ""
			content_type = "text/html"
			file_path = file_path[1:]
			server_address = headers.get("Host")
			Agent = "HPCustomWebProxy"
			responsequeue = queue.Queue()
			
			#creating request message
			http_get_request = "GET /"+file_path+" HTTP/1.1\r\n" + "Host: "+server_address+"\r\n" + "Connection: close\r\n" + "User-Agent: "+Agent+"\r\n\r\n"
			
			#starting proxy - server communication on new thread
			threading.Thread(target = server_communication_handler, args = (http_get_request,server_address,80,responsequeue)).start()
			
			#fetching response from responsequeue and sending it to the client
			a = responsequeue.get()
			connection.send(a)
	except error as e:
		print(f"Request send / Response receive failure: {e}")
	try:
		connection.close()
	except error as e:
		print("Connection closing error: {e}")
			
#main function
def main():
	#creating and binding socket on 8080
	try:
		ssocket = socket(AF_INET,SOCK_STREAM)
		ssocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
		ssocket.bind(('',8080))
		ssocket.listen(10)
		print("Server started listening...")
	except error as e:
		print(f"Socket creation or binding failure: {e}")
	
	#accepting clients connection and sending it on the separate new thread
	try:
		while True:
			connection,address = ssocket.accept()
			threading.Thread(target = client_communication_handler, args = (connection,address)).start()
			print("Active client on separate threads : ", threading.active_count()-1)
	except error as e:
		print("Socket error while accepting connection: {e}")
	try:    
		ssocket.close()
		print("Server close all connections and stops listening...")
	except error as e:
		print("Socket closing error: {e}")
main()
