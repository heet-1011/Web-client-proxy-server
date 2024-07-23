from socket import *				#import socket for tcp connection
import threading					#import threading for handling each client connection on new thread
import os							#import os to check the file system to fetch the file 
from time import gmtime, strftime	#import time to get the time
import magic						#import magic to know file MIME type

#function which handles client communication
def client_communication_handler(connection,address):
	print("Client connection with address : ",connection)
	
	#getting data from client
	try:
		request = connection.recv(1024)
		request = request.decode()
		print(request)
		
		#splitting request
		request_breakdown = request.split("\r\n")
		
		#splitting 1st line of request in request_method, file_path, protocol
		request_method, file_path, protocol = request_breakdown[0].split()
		
		#splitting all headers
		headers = {}
		for i in request_breakdown[1:]:
			if i:
				#each header split into key value pair and storing it into dicionary
				header_name, header_value = i.split(": ")
				headers[header_name] = header_value
		
		#dealing GET request
		if(request_method == "GET"):
			modified_time = ""
			if(file_path.find("://")!=-1):
				file_path = file_path[file_path.find("://")+3:]
			host, file_path = file_path.split("/",1)
			
			#checking if file exist
			if(os.path.isfile(file_path) == True):
				
				#reading file content and store it into variable
				with open(file_path, "r", encoding="utf-8") as file:	
					file_content = file.read()
					
				#getting file MIME type
				content_type = magic.from_file(file_path,mime=True)
				
				#getting file last modified time and file content length
				modified_time = strftime("%a, %d %b %Y %I:%M:%S %p", gmtime(os.path.getmtime(file_path)))
				content_length = len(file_content)
				response_code = "200"
				response_msg = "OK"
			else:
				#creating attribute as 404 NOT found when requested file not found in host place
				file_content = "<html><head><style>body {display: flex;flex-direction: column;justify-content: center;align-items: center;height: 100vh;}h1 {font-size: 2.5rem;}</style></head><body><h1>404 File Not Found</h1></body></html>"
				content_type = "text/html"
				response_code = "404"
				response_msg = "File Not Found"
				content_length = len(file_content)
			
			#getting time at which response is created	
			response_time = strftime("%a, %d %b %Y %I:%M:%S %p", gmtime())	
			
			#creating response message
			http_get_response = "HTTP/1.1 "+response_code+" "+response_msg+"\r\n" + "Date: "+response_time+" GMT\r\n" + "Connection: close\r\n" + "Server: HPCustomServer\r\n" +  "Last-Modified: "+modified_time+" GMT\r\n" + "Content-Length: "+str(content_length)+"\r\n" + "Content-Type: "+content_type+"\r\n\r\n" + file_content
		
		#sending response to client
		connection.send(http_get_response.encode())
	except error as e:
		print(f"Request send / Response receive failure: {e}")
	try:
		connection.close()
	except error as e:
		print("Connection closing error: {e}")
		
#main function
def main():
	#creating and binding server to listen on 80 port
	try:
		ssocket = socket(AF_INET,SOCK_STREAM)
		ssocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
		ssocket.bind(('',80))
		ssocket.listen(10)
		print("Server started listening...")
	except error as e:
		print(f"Socket creation or binding failure: {e}")
	
	#accepting clients connection and sending it on separate thread to work
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
