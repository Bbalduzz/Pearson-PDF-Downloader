import requests, json, os, shutil, fitz
from concurrent.futures import ThreadPoolExecutor, as_completed

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
		toc = []
		assets = requests.get('https://prism.pearsoned.com/api/contenttoc/v1/assets', params=params, headers=headers).json()
		for j in assets['children']:
			try:
				toc.append([int(j['level']), j['title'], int(j['pageno'])-1])
				if j.get('children') != None:
					for i in j['children']:
						toc.append([int(i['level']), i['title'], int(i['pageno'])-1])
			except: break
		return toc

meta = Metadata()

def progress_bar(progress, total):
    percent = 100 * (progress / float(total))
    bar = '█' * int(percent) + '-' * (100 - int(percent))
    print(f'\r[+] Downloading book... |{bar}| {percent:.2f}%', end='\r')

def get_page(n):
    uuid = meta.uuid()
    page_data = requests.get(f'https://etext-content.gls.pearson-intl.com/eplayer/pdfassets/prod1/{prodid}/{uuid}/pages/page{n}', headers={'Cookie': page_cookie, 'token': bearer_token}).content
    page_doc = fitz.open(stream=page_data, filetype="png")
    pdfbytes = page_doc.convert_to_pdf()
    return fitz.open("pdf", pdfbytes)

def dl():
    uuid = meta.uuid()
    pagenum = meta.npages()
    book = meta.id()
    toc = meta.toc()
    print(f'''
    [+] Book found:
        - title: {book["title"]}
        - author: {book["author"]}
        - pages: {str(pagenum)}
    ''')
    doc = fitz.Document()
    pages = []
    next_page_to_add = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_page, n): n for n in range(pagenum)}
        for future in as_completed(futures):
            n = futures[future]
            try:
                page = future.result()
                pages.append((n, page))
                pages.sort()
                while pages and pages[0][0] == next_page_to_add:
                    _, page = pages.pop(0)
                    doc.insert_pdf(page)
                    next_page_to_add += 1
                    progress_bar(next_page_to_add, pagenum)
            except Exception as exc:
                print(f'Page {n} generated an exception: {exc}')
    doc.set_toc(toc)
    doc.save(f'{book["title"]}.pdf')

dl()
