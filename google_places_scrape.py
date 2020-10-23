from bs4 import BeautifulSoup
import requests, os, csv, urllib.parse, urllib3, time, random, pathlib
from lxml.html import fromstring
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

urllib3.disable_warnings()

retry_strategy = Retry(
    total=20,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"],
    backoff_factor=2
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

def get_proxies():
    proxyList = set()
    if int(os.getenv("id")) == 0:
        proxyList = ('1.20.101.24:51681', '188.165.16.230:3129', '185.189.211.70:8080', '113.130.126.212:53529',
         '62.210.207.107:3838', '181.225.213.226:999', '51.75.147.40:3128', '119.82.241.199:8080',
         '103.102.14.128:8080', '103.15.167.37:41787')
    else:
        try:
            url = 'https://free-proxy-list.net/'
            response = requests.get(url)
            parser = fromstring(response.text)
            for i in parser.xpath('//tbody/tr')[:10]:
                if i.xpath('.//td[7][contains(text(),"yes")]'):
                    #Grabbing IP and corresponding PORT
                    proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                    proxyList.add(proxy)
        except:
            return None
    return proxyList

# def writeToDB(result):
#     with psycopg2.connect("postgresql://postgres:postgres@db/google_business_cards") as conn:
#         with conn.cursor() as cur:
#             try:
#                 cur.execute(f"INSERT INTO business_cards(cis_name, search_name, matching_name, industry) VALUES ('{cleanNames(str(result.get('cis_name', '')))}', '{cleanNames(str(result.get('search_name', '')))}', '{cleanNames(str(result.get('matching_name', '')))}', '{cleanNames(str(result.get('industry', '')))}')")
#             except (Exception, psycopg2.DatabaseError) as error:
#                 print(f"DB Error - {error}")
#
# def checkExistingInDB(name):
#     with psycopg2.connect("postgresql://postgres:postgres@db/google_business_cards") as conn:
#         with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
#             try:
#                 cur.execute(f"SELECT * FROM business_cards WHERE business_cards.search_names LIKE '%{cleanNames(name)}%'")
#                 return cur.fetchone()
#             except (Exception, psycopg2.DatabaseError) as error:
#                 print(error)
#                 return None

def loadCompanyNames(fileLocation):
    lastCheckpoint = getLastCheckpoint()
    lastId = lastCheckpoint.get("id",-1)
    with open(fileLocation, mode='r', newline='\n', encoding='utf-8') as infile:
        csv_reader = csv.DictReader(infile, delimiter=',', quotechar='"')
        for row in csv_reader:
            if int(row[""]) > int(lastId):
                yield {"id":str(row[""]) , "file":f"{os.getenv('input_file')}","name":str(row['CUST_FULL_NAME_1'])}
            else:
                continue

def writeToCsv(result):
    with open(os.path.join("data", "output", f"out_{os.getenv('input_file')}"), mode='a+', newline='\n',
              encoding='utf-8') as infile:
        writer = csv.DictWriter(infile, result.keys())
        writer.writerow(result)

def updateCheckpoint(id):
    with open(os.path.join("data", "checkpoints", f"checkpoint_{os.getenv('input_file')}"), mode='w+', newline='\n',
              encoding='utf-8') as infile:
        writer = csv.DictWriter(infile, ["id","fileName"])
        writer.writeheader()
        writer.writerow({"id":f"{str(id)}", "fileName":f"{os.getenv('input_file')}"})

def getLastCheckpoint():
    try:
        with open(os.path.join("data", "checkpoints", f"checkpoint_{os.getenv('input_file')}"), mode='r', newline='\n',
                  encoding='utf-8') as infile:
            csv_reader = csv.DictReader(infile, delimiter=',', quotechar='"')
            for row in csv_reader:
                if row:
                    return row
                else:
                    break
            else:
                return {}
    except FileNotFoundError:
        return {}
    except FileExistsError:
        return {}


def buildSearchUrl(queryInput):
    return f"https://google.com/search?q={urllib.parse.quote(queryInput)}"

def parse_listing(url, proxies):
    time.sleep(random.uniform(0.25,1.75))
    req = http.get(url,
                   headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0'},
                   verify=False)

    if req:
        soup = BeautifulSoup(req.content, 'lxml')
    else:
        return None
    if not soup:
        return None
    else:
        div = soup.find("div", class_="SPZz6b")
        name = None
        if div:
            for tag in div:
                if tag.attrs.get("data-attrid") == 'title':
                    name = tag.string
                    break
                else:
                    name = None
        else: name = None

        industry = soup.find("span", class_='YhemCb')
        if industry: industry = industry.text
        else: industry = None

        if name or industry:
            return {"name":name, "industry":industry}
        else:
            return None

def cleanBusinessName(name):
    if "*" in name: return True, name.replace("*", "").replace("/", "_")
    else: return False, f"{name} skip individual"

def cleanNames(name):
    return name.replace("`","").replace("'","")[:499]

def run():
    for i, record in enumerate(loadCompanyNames(os.path.join("data","input",f"{os.getenv('input_file')}"))):
        company, businessName = cleanBusinessName(record.get("name"))
        if company:
            outcome = parse_listing(buildSearchUrl(businessName), None)
            if outcome:
                result = {"file": os.getenv('input_file'), "id": str(record.get("id")),
                          "cis_name": record.get("name"), "search_name": businessName,
                          "matching_name": outcome.get("name"), "industry": outcome.get("industry")
                          }
                print(f"{str(record.get('id'))} > {record.get('name')} > {outcome.get('name')} - {outcome.get('industry')}")
            else:
                result = {"file": os.getenv('input_file'), "id": str(record.get("id")),
                          "cis_name": record.get("name"), "search_name": businessName,
                          "matching_name": None, "industry": None
                          }
                print(f"{str(record.get('id'))} > {businessName} no match")
            writeToCsv(result)
        else:
            print(f"{str(record.get('id'))} > {businessName}")

        updateCheckpoint(record.get("id"))

run()