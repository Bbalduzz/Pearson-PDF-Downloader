import requests, json, os, shutil
import fitz

url = input('[+] Enter book URL:\n')
prodid = url.split('/')[4]

with open('cookies.txt', 'r') as f:
	bearer_token, page_cookie = f.read().splitlines()
headers = {'x-authorization': bearer_token}
params = {'productId': prodid}

class Metadata:
	def __init__(self):
		pass
	def id(self):
		infos = requests.get(f'https://etext-ise.pearson.com/marin/api/1.0/products/{prodid}', headers={'authorization': f'Bearer {bearer_token}'}).json()
		book = {
			'title': infos['title'],
			'author': infos['authors'],
		}
		return book
	def uuid(self):
		infos = requests.get(f'https://etext-ise.pearson.com/marin/api/1.0/products/{prodid}', headers={'authorization': f'Bearer {bearer_token}'}).json()
		server_side_uuid = infos['serverSideUuid']
		return server_side_uuid
	def npages(self):
		assets = requests.get('https://prism.pearsoned.com/api/contenttoc/v1/assets', params=params, headers=headers).json()
		return int(assets['slates'][-1]['pageno'])
	def toc(self):
		assets = requests.get('https://prism.pearsoned.com/api/contenttoc/v1/assets', params=params, headers=headers).json()

meta = Metadata()

def progress_bar(progress, total):
    percent = 100 * (progress / float(total))
    bar = '█' * int(percent) + '-' * (100 - int(percent))
    print(f'\r[+] Downloading book... |{bar}| {percent:.2f}%', end='\r')

def dl():
	uuid = meta.uuid()
	pagenum = meta.npages()
	book = meta.id()
	print(f'''
[+] Book found:
	- title: {book["title"]}
	- author: {book["author"]}
	- pages: {str(pagenum)}
''')
	doc = fitz.Document()
	progress_bar(0, pagenum)
	for n in range(pagenum):
		page_data = requests.get(f'https://etext-content.gls.pearson-intl.com/eplayer/pdfassets/prod1/{prodid}/{uuid}/pages/page{n}', headers={'Cookie': page_cookie, 'token': bearer_token}).content
		page_doc = fitz.open(stream=page_data, filetype="png")
		pdfbytes = page_doc.convert_to_pdf()
		doc.insert_pdf(fitz.open("pdf",pdfbytes))
		progress_bar(n, pagenum)
	doc.save(f'{book["title"]}.pdf')

dl()