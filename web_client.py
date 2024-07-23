from socket import *	#import socket for creating tcp socket
import re		#import re for using regex function to identify links in body of http response
import ssl		#import to work on https link over secure socket layer


#function that parse the response
def parse_response(response, server_address, server_port, file_path):
	#splitting headers and body
	response,body = response.split(b'\r\n\r\n',1)
		
	#splitting headers and store it to list
	response_breakdown = response.split(b'\r\n')
		
	#splitting 1st header line in 3 variable protocol, response code, response_msg
	protocol, response_code, response_msg = response_breakdown[0].split(b' ',2)
		
	print("http response")
	print("File_path: ",file_path)
	print("Response Code : ", response_code.decode())
	print("Response Message : ", response_msg.decode())
		
	#if response code is 200 then parsing the headers to understand the response and body to get external links 
	if(response_code == b'200'):
		headers = {}
		for i in response_breakdown[1:-1]:
			if i:
				#print(i.decode())
				#splitting each headers into header attribute and value and store it into dictionary
				header_name, header_value = i.split(b": ",1)
				headers[header_name] = header_value
		global flag
		if(flag==1):
			file_ext = file_path.split('.')
			media_ext = ['jpg', 'jpeg', 'png', 'svg','gif', 'bmp', 'mp3', 'wav', 'mp4', 'avi']
			if not (file_ext[-1] in media_ext):
				flag = flag - 1
					
				#using regex to find urls inside the body (refrence links)
				link_regex = rb'(?:href|src)="([^"]*)"'
				link_found = re.findall(link_regex, body)
				if(len(link_found)!=0):

					#for each found refrence links find host and path
					for i in link_found:
						print("External Links : ",i.decode())
						print("-"*50+"\n")
						find_host_and_fpath(i,server_address,server_port)

def req_reply(csocket,server_address,server_port,file_path):
	#creating http get request
	http_get_request = "GET /"+file_path+" HTTP/1.1\r\n" + "Host: "+server_address+"\r\n" + "Connection: close\r\n" + "User-Agent: "+"HPCustomClient"+"\r\n\r\n"
	print("http get request")
	print(http_get_request)
	print("-"*25)
	try:
		#sending http get request
		csocket.send(http_get_request.encode())
		
		#getting http response from server
		http_get_response = b""
		while True:
			upcoming_data = csocket.recv(1024)
			if not upcoming_data:
				break
			http_get_response += upcoming_data
		
		parse_response(http_get_response, server_address, server_port, file_path)
		
	except error as e:
		print(f"Request send / Response receive failure: {e}")
	try:
		csocket.close()
	except error as e:
		print("Socket closing error: {e}")

#this function deals with the https request reply		
def req_reply_https(csocket,server_address,server_port,file_path):
	https_get_request = "GET /"+file_path+" HTTP/1.1\r\n" + "Host: "+server_address+"\r\n" + "Connection: close\r\n" + "User-Agent: "+"HPCustomClient"+"\r\n\r\n"
	print("https get request")
	print(https_get_request)
	print("-"*25)
	csocket.send(https_get_request.encode())
	https_response = b''
	response = csocket.recv(1024)
	while response:
		https_response += response
		response = csocket.recv(1024)
	parse_response(https_response, server_address, server_port, file_path)
	csocket.close()
	
#decode the byte to string
def chk_and_decode(attribute):
	if isinstance(attribute,bytes):
		attribute = attribute.decode()
	return attribute
	
#getting host and file path from the url
def find_host_and_fpath(link,server_address,server_port):
		#splitting https:// or http:// from url
		if(link.startswith(b"https")):
			server_port = 443
		elif(link.startswith(b"http")):
			server_port = 80
		if(link.find(b"://")!=-1):
			link = link[link.find(b"://")+3:]
		#splitting host and file path from url
		if b"/" in link:
			host, file_path = link.split(b"/",1)
		else:
			host=b""
			file_path = link
		
		#splitting address and port
		if(host!=b""):
			host = host.split(b":")
			server_address = host[0]
			if(len(host)==2):
				server_port = host[1]
		
		#create new socket and get file from server for refrenced link file
		connect_server(chk_and_decode(server_address), chk_and_decode(server_port), chk_and_decode(file_path))

#wrap tcp socket with ssl
def create_ssl_socket(socket,server_address):
	#ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
	socket = ssl.create_default_context().wrap_socket(socket, server_hostname=server_address, server_side=False)
	return socket

#creating socket and connecting it to host or proxy as per the configuration
def connect_server(server_address, server_port, file_path):
	try:
		csocket = socket(AF_INET, SOCK_STREAM)
		
		#if proxy not set than connect directly with server else connect to proxy
		if proxy_address == None:
			csocket.connect((server_address, server_port))
		else:	
			csocket.connect((proxy_address, proxy_port))
		if(server_port==80):
		#send and receive data over above created socket
			req_reply(csocket,server_address,server_port,file_path)
		elif(server_port==443 and proxy_address==None):
			csocket = create_ssl_socket(csocket,server_address)
			req_reply_https(csocket,server_address,server_port,file_path)
			
	except error as e:
		print(f"Socket creation failure: {e}")
	
#main function
def main():
	n = int(input("Enter 1: To request web-proxy\n      2: To request web-server directly.\n"))
	global flag
	flag = 1
	
	#fetching connection details
	server_address = input("Enter Server's IP address : ")
	server_port = int(input("Enter Server's port no : "))
	file_path = input("Enter the file name which you have to fetch : ")
	global proxy_address 
	proxy_address = None 
	global proxy_port
	proxy_port = None
	if(n==1):
		proxy_address = input("Enter Proxy-Server's IP address : ")
		proxy_port = int(input("Enter Proxy-Server's port no : "))
	print("-"*50)
	
	#dealing with empty values entered by user
	if(file_path==""):
		file_path="/"
	if(server_address=="" or server_port=="" or proxy_address=="" or proxy_port==""):
		print("Some field is empty")
		main()
	else:
		connect_server(server_address, server_port,file_path)
main()
