from bs4 import BeautifulSoup
import requests, os, csv, urllib.parse, urllib3, time, random
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
    proxyList = [
        {"http":"169.159.179.248:8080"}, {"http":"105.208.17.58:8080"}, {"http":"160.119.44.210:8080"}, {"http":"196.214.145.106:80"},
        {"https":"41.194.37.106:45381"},{"https":"41.222.159.191:8080"},{"https":"66.251.179.207:8080"}
        ]
    return proxyList

def rotate_proxy(proxies):
    proxy_select = random.randint(-1,len(proxies)-1)
    if proxy_select < 0 or os.getenv('proxy_enabled', default=False):
        time.sleep(random.uniform(0.5, 1.25))
        return None
    else:
        print(f"Proxy -> {proxies[proxy_select].get('http','')}{proxies[proxy_select].get('https','')}")
        return proxies[proxy_select]

def get_user_agents():
    userAgents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv: 82.0) Gecko/20100101 Firefox/82.0",
        "Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36 Edg/86.0.622.63"
        ]
    return userAgents

def rotate_user_agent(userAgents):
    return userAgents[random.randint(0,len(userAgents)-1)]

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


def makeRequest(url, header,proxy):
    return http.get(url, headers=header, proxies=proxy, verify=False)


def parse_listing(url, proxies):
    proxy = rotate_proxy(proxies)
    user_agent = rotate_user_agent(get_user_agents())
    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
               'Accept-Language': 'en-US,en;q=0.9,af;q=0.8',
               'Accept-Encoding': 'gzip, deflate, br',
               'Connection': 'keep-alive',
               'Upgrade-Insecure-Requests': '1',
               'User-Agent': user_agent}
    try:
        req = makeRequest(url, headers, proxy)
    except:
        return None

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

def cleanName(name):
    strName = name.lower()
    strName = strName.replace("(", "").replace(")", "")
    strName = strName.replace("pty","").replace("ltd","").replace("(ltd)","")
    strName = strName.replace("pty ltd", "").replace("pty(ltd)", "")
    strName = strName.replace("cc", "").replace("cc.", "")
    strName = strName.replace("pty.", "").replace("ltd.", "")
    return strName.capitalize()

def cleanBusinessName(name):
    if "*" in name: return True, cleanName(name.replace("*", "").replace("/", "_"))
    else: return False, f"{name} skip individual"


def run():
    for i, record in enumerate(loadCompanyNames(os.path.join("data","input",f"{os.getenv('input_file')}"))):
        company, businessName = cleanBusinessName(record.get("name"))
        if company:
            outcome = parse_listing(buildSearchUrl(businessName), get_proxies())
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