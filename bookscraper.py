import requests, sys, csv
from bs4 import BeautifulSoup
import concurrent.futures

#Set max threads we are allowed to use
MAX_THREADS = 30
#global list that is used to store data of URL's
csvList = []
masterList = []

def findAllProductPages(url):
    #get page and find all h3 tags in the page, requests.get(url) should never return null
    page = requests.get(url)
    soup = BeautifulSoup(page.text,"html.parser")
    names = soup.findAll("h3")

    #loop through all the h3 tags and store the hrefs in a list
    for i in range(0,len(names)):
        names[i] = str(names[i])
        start = names[i].find("href=")
        end = names[i].find(" ",start)
        names[i]= names[i][start+12:end-1]
        masterList.append(names[i])

def getPageInfo(url):
    #request the page based on passed URL
    page = requests.get(f"http://books.toscrape.com/catalogue/{url}")
    page.encoding = 'utf-8'
    soup = BeautifulSoup(page.text, "html.parser")
    #use Beautiful Soup to find the title,price,stock,rating, and description of the book
    title = str(soup.find("h1").find(string=True))
    price = str(soup.find("p",attrs={"class":"price_color"}).find(string=True))
    price = price.replace("Â","")
    stock = str(soup.find("p",attrs={"class":"instock availability"}))
    start = stock.find("In stock")
    end = stock.find(" ",start+10)
    stock = int(stock[start+10:end])
    rating = str(soup.findAll("div",attrs={"class":"col-sm-6 product_main"}))
    start = rating.find('class="star-rating ')
    end = rating.find('"',start+7)
    rating = rating[start+19:end]
    if rating == "One":
        rating = 1
    elif rating == "Two":
        rating = 2
    elif rating == "Three":
        rating = 3
    elif rating == "Four":
        rating = 4
    elif rating == "Five":
        rating = 5
    desc = str(soup.find("p", attrs={"title":None , "class":None}))
    desc = desc.replace("...more","")
    desc = desc.replace("<p>","")
    desc = desc.replace("</p>","")
    #append the data to csvList
    csvList.append([title,price,rating,desc,stock])
    
def myFunc(e):
    #used to sort the list based on rating
    return e[2]*-1   

def main():
    print("Scraping site...")
    #loop through all 50 pages and grab all the URL's we need to visit, then place it into the master list
    toFind = []
    for i in range(1,51):
        toFind.append(f"http://books.toscrape.com/catalogue/category/books_1/page-{i}.html")
    threads = min(MAX_THREADS, len(toFind))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(findAllProductPages, toFind)
    #Sets the amount of threads that will be used
    threads = min(MAX_THREADS, len(masterList))
    #Multithreading for all the URL's
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(getPageInfo, masterList)
    
    #sort the list based on rating, then write it to the csv file.
    csvList.sort(key=myFunc)
    try:
        file = open("scraped_books.csv", "w", newline='')
    except PermissionError:
        print("ERROR: Cannot access file. Try closing the file if it is open")
        sys.exit()

    writer = csv.writer(file,dialect='excel')
    writer.writerow(["TITLE","PRICE","RATING","DESCRIPTION","STOCK"])    
    for i in range(0,len(csvList)):
        #Throw error if page has any characters that can't be encoded.
        try:
            writer.writerow(csvList[i])
        except UnicodeEncodeError:
            print("ERROR: cannot print invalid character")
    file.close()
    print("Scraped Data!")
main()