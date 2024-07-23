from socket import *				#import socket to create tcp connections
import threading					#import threading to handle clients and servers on separate threads
import time							#import time to fetch current time
from time import gmtime, strftime	
import queue						#import queue to use as message passing between two threads
import re							#import re to use regex to find keywords
import os							#import os to deal with file system
import matplotlib.pyplot as plt		#import matplotlib to plot the web statistics on pie chart

#print_statistics function deal with ploting pie chart
#this function plot two chart one is no of time particular link accessed through proxy and another is no of time particular user access proxy
def print_statistics():
	lst = [i for j in user_session_track.values() for i in j]
	link_refrence_counts = {}
	for i in lst:
		if i in link_refrence_counts:
			link_refrence_counts[i] += 1
		else:
			link_refrence_counts[i] = 1
	users_link_access_count = {}
	for k,v in user_session_track.items():
		users_link_access_count[k] = len(v)
	fig,axes = plt.subplots(1,2,figsize = (10,6))
	axes[0].pie(list(link_refrence_counts.values()),labels=list(link_refrence_counts.keys()))
	axes[0].set_title("Proxy Statistics")
	axes[1].pie(list(users_link_access_count.values()),labels=list(users_link_access_count.keys()))
	axes[1].set_title("Users Access Statistics")
	plt.tight_layout()
	plt.show()

#function that handle proxy - server communication	
def server_communication_handler(http_get_request,server_address,server_port,responsequeue,keyword_blacklist):
	#creating socket for proxy - server communication
	try:
		csocket = socket(AF_INET, SOCK_STREAM)
	except error as e:
		print(f"Socket creation failure: {e}")
	
	#connecting socket to server
	try:
		csocket.connect((server_address, server_port))
	except error as e:
		print(f"Socket connection failure: {e}")
	
	#sending request to server
	try:
		csocket.send(http_get_request.encode())
		
		#receiving response from server
		http_get_response = b""
		while True:
			upcoming_data = csocket.recv(1024)
			if not upcoming_data:
				break
			http_get_response += upcoming_data
		
		#parsing response headers and body
		index = http_get_response.find(b"\r\n\r\n")
		response_breakdown = http_get_response[:index]
		file_content = http_get_response[index:]
		response_breakdown = response_breakdown.decode()
		response_breakdown = response_breakdown.split("\r\n")
		protocol, response_code, response_msg = response_breakdown[0].split(' ',2)
		
		#splitting headers furthermore and storing it as key value pairs
		headers = {}
		for i in response_breakdown[1:-1]:
			if i:
				header_name, header_value = i.split(": ")
				headers[header_name] = header_value
				
		#dealing with responses
		if(response_code == '200'):
			try:
				#decoding the file content and then shading the blocked keywords
				
				file_content = file_content.decode()
				print(file_content)
				regex_blacklist = r'\b(?:' + '|'.join(re.escape(word) for word in keyword_blacklist) + r')\b'
				def shade_blacklisted_keyword(keyword):
					word = keyword.group()
					return "*" * len(word)
				modified_file_content = re.sub(regex_blacklist, shade_blacklisted_keyword, file_content)
				response_time = strftime("%a, %d %b %Y %I:%M:%S %p", gmtime())
					
				#creating modified reponse with shaded keywords
				http_get_response = "HTTP/1.1 "+response_code+" "+response_msg+"\r\n" + "Date: "+response_time+" GMT\r\n" + "Connection: close\r\n" + "Server: HPCustomServer\r\n" +  "Last-Modified: "+str(headers.get("Last-Modified"))+" GMT\r\n" + "Content-Length: "+str(headers.get("Content-Length"))+"\r\n" + "Content-Type: "+str(headers.get("Content-Type"))+"\r\n\r\n" + modified_file_content
				print(http_get_response)
				http_get_response = http_get_response.encode()
			except error as e:
				print(f"Error: {e}")
			print("Response Code 200 OK")
		elif(response_code == '404'):
			print("Error 404 Not Found")
		elif(response_code == '304'):
			print("Response Code 304 Not Modified")
		elif(response_code == '301'):
			print("Response Code 301 Moved Permanently")
		responsequeue.put(http_get_response)
	except error as e:
		print(f"Request send / Response receive failure: {e}")
	try:	
		csocket.close()
	except error as e:
		print("Socket closing error: {e}")

#function that handle client - proxy communication	
def client_communication_handler(connection,address,site_blacklist,keyword_blacklist):
	print("Client connection with address : ",address)
	
	#receiving request from the client
	try:    
		request = connection.recv(1024)
		request = request.decode()
		print(request)
		
		#parsing clients request
		request_breakdown = request.split("\r\n")
		request_method, file_path, protocol = request_breakdown[0].split(' ',2)
		
		#breakdown headers and store them as key, value pair in dictionary
		headers = {}
		for i in request_breakdown[1:]:
			if i:
				header_name, header_value = i.split(": ")
				headers[header_name] = header_value
		server_address = headers.get("Host")
		
		#storing clients history to show web statistics
		if address[0] not in user_session_track:
			user_session_track[address[0]] = []
		user_session_track[address[0]].append(server_address)
		
		#check clients requested website is blacklisted or not if blacklisted than sending 403 Access Denied response
		if(server_address in site_blacklist):
			print("Client ask for Blacklisted site "+server_address)
			response_time = strftime("%a, %d %b %Y %I:%M:%S %p", gmtime())
			a = http_get_response = "HTTP/1.1 "+'403'+" "+'Forbidden'+"\r\n" + "Date: "+response_time+" GMT\r\n" + "Connection: close\r\n" + "Server: HPProxyServer\r\n\r\n"
			a = a.encode()
		else:
		#creating request which is to be send to server on new thread
			if(request_method == "GET"):
				modified_time = ""
				content_type = "text/html"
				file_path = file_path[1:]
				Agent = "HPCustomWebProxy"
				
				#creating responsequeue for message passing
				responsequeue = queue.Queue()
				http_get_request = "GET /"+file_path+" HTTP/1.1\r\n" + "Host: "+server_address+"\r\n" + "Connection: close\r\n" + "User-Agent: "+Agent+"\r\n\r\n"
				
				#starting server communication on new thread
				threading.Thread(target = server_communication_handler, args = (http_get_request,server_address,80,responsequeue,keyword_blacklist)).start()
				
				#fetching response from queue 
				a = responsequeue.get()
				
		#sending final response to client
		connection.send(a)
	except error as e:
		print(f"Request send / Response receive failure: {e}")
	try:
		connection.close()
	except error as e:
		print("Connection closing error: {e}")
	
	#on terminating connection if wait for 5 seconds and if no new connection come than it print web statistics interms of pie plot.
	time.sleep(5)
	if(threading.active_count()-1==1):
		print_statistics()

#main function
def main():
	#getting blacklisted website and blacklisted keywords from user
	global user_session_track
	user_session_track = {}
	site_blacklist = input("Enter website separated with comma to be blacklisted :\n").split(",")
	keyword_blacklist = input("Enter keyword separated with comma to be shade out :\n").split(",")
	print(site_blacklist)
	print(keyword_blacklist)
	
	#creating and binding socket on port 8080
	try:
		ssocket = socket(AF_INET,SOCK_STREAM)
		ssocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
		ssocket.bind(('',8080))
		ssocket.listen(10)
		print("Proxy started listening...")
	except error as e:
		print(f"Socket creation or binding failure: {e}")
		
	#accepting clients connection and sending it on separate thread
	try:	
		while True:
			connection,address = ssocket.accept()
			threading.Thread(target = client_communication_handler, args = (connection,address,site_blacklist,keyword_blacklist)).start()
			print("Active client on separate threads : ", threading.active_count()-1)
	except error as e:
		print("Socket error while accepting connection: {e}")
	
	#closing proxy socket on which it is listening
	try:
		ssocket.close()
		print("Server close all connections and stops listening...")
	except error as e:
		print("Socket closing error: {e}")
main()
