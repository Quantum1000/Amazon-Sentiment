from selenium import webdriver as wd
from selenium.webdriver.common.keys import Keys
import random
import pickle
from bs4 import BeautifulSoup as bs
import time

LETTER = ['e', 't', '.']

EN = {'SITE':'https://www.amazon.com', 'SEARCH1':'/s?k=', 'SEARCH2':'&s=review-count-rank'}
JP = {'SITE':'https://www.amazon.co.jp', 'SEARCH1':'/s?k=', 'SEARCH2':'&s=review-count-rank'}
DE = {'SITE':'https://www.amazon.de', 'SEARCH1':'/s?k=', 'SEARCH2':'&s=review-count-rank&__mk_de_DE=ÅMÅŽÕÑ&'}
TR = {'SITE':'https://www.amazon.com.tr', 'SEARCH1':'/s?k=', 'SEARCH2':'&s=review-count-rank&__mk_tr_TR=ÅMÅŽÕÑ'}
LANGS = {'EN':EN, 'JA':JP, 'DE':DE, 'TR':TR} # , 
options = wd.ChromeOptions()
# Parameters:
RvPL = 50000 # Reviews per Language
RvPP = 100 # Maximum reviews per product
#options.binary_location = 'C:/ChromeDriver'
options.add_argument('headless')
options.add_argument('window-size=1200x600')
driver = wd.Chrome('C:/ChromeDriver/chromedriver', chrome_options=options)
print("Hello, world!")
for lang in LANGS:
    SITE = LANGS[lang]['SITE']
    SEARCH1 = LANGS[lang]['SEARCH1']
    SEARCH2 = LANGS[lang]['SEARCH2']
    # Start from previous data, if it exists.
    allreviews = []
    prodlist = []
    try:
        fppl = open('prodlist' + lang + '.pkl', "rb")
        fpr = open('reviews' + lang + '.pkl', "rb")
    except FileNotFoundError:
        print('No existing review data, starting new.')
    else:
        prodlist = pickle.load(fppl)
        allreviews = pickle.load(fpr)
        print('Loaded ' + str(len(allreviews)) + ' reviews from saved review data.')
    savedreviews = len(allreviews)
    ltri = 0
    if(len(allreviews) > RvPL):
        continue
    driver.get(SITE + SEARCH1 + LETTER[0] + SEARCH2)
    content = driver.page_source
    soup = bs(content, 'lxml')
    # Test for Captcha, and ask the human for help if one shows up.
    testCaptcha = soup.find('form', {'action':"/errors/validateCaptcha"})
    if not testCaptcha is None:
        with open('captcha.html', "w") as fp:
            fp.write(content)
        captchabox = driver.find_element_by_id('captchacharacters')
        captchabox.send_keys(input("captcha.html saved. Please read and enter captcha: "))
        captchabox.send_keys(Keys.RETURN)
    fppl = 0
    fpr = 0
    while len(allreviews) < RvPL:
        i = 1
        ltr = LETTER[ltri % len(LETTER)]
        if ltri == 3:
            break
        ltri += 1

        # Loops once for each results page. It would probably be better to limit the number of products per search than result pages, but w/e
        while len(allreviews) < RvPL and i < 60:
            driver.get(SITE + SEARCH1 + ltr + SEARCH2 + "&page=" + str(i))
            content = driver.page_source
            soup = bs(content,'lxml')
            # Progress
            print('Started page #' + str(i) + ' for search term "' + ltr + '" and language "' + lang + '". Gathered ' + str(len(allreviews)) + ' reviews.')
            i += 1
            for product in soup.findAll('span', {"cel_widget_id":"SEARCH_RESULTS-SEARCH_RESULTS"}, True):
                if len(allreviews) > RvPL:
                    break
                # Check for and ignore sponsored results, as they could affect the data.
                sponsoredtest = product.find('div', {'data-component-type':'sp-sponsored-result'})
                if not sponsoredtest is None:
                    continue
                url = (SITE + product.findAll('a', {"class":"a-link-normal"}, limit=2)[1].attrs['href'])
                dploc = url.find('/dp/')
                prodcode = url[dploc + 4:url.find('/', dploc + 4)]
                if prodcode in prodlist:
                    continue
                prodlist.append(prodcode)

                driver.get(url)
                content = driver.page_source
                soup = bs(content, 'lxml')

                prodname = url[len(SITE)+1:url.find('/dp')]
                prodcat = ''
                prodcathtml = soup.find('div', {'id':'nav-subnav'})
                if prodcathtml is None:
                    # This particular retrieval technique definetly doesn't work with prime video, so assume that's why it failed.
                    prodcat = 'instant-video'
                else:
                    prodcat = prodcathtml.attrs['data-category']

                nexturlhtml = soup.find('a', attrs={'data-hook':'see-all-reviews-link-foot'})
                if nexturlhtml is None:
                    continue
                nexturl = SITE + nexturlhtml.attrs['href']

                prodreviews = []
                while len(prodreviews) < RvPP*5:
                    driver.get(nexturl)
                    content = driver.page_source
                    soup = bs(content, 'lxml')
                    for review in soup.findAll('div', attrs={'data-hook':'review'}):
                        # Review Content format = [category, name, rating, title, text]
                        reviewcontent = [prodcat, prodname]
                        reviewrating = review.find('i', attrs={'data-hook':'review-star-rating'})
                        if reviewrating is None:
                            continue
                        ratingclass = reviewrating.attrs['class']
                        foundone = False
                        for s in ratingclass:
                            if s.find('a-star-') != -1:
                                rating = int(s[::-1][0])
                                foundone = True
                        if not foundone:
                            print("empty review")
                            continue
                        reviewcontent.append(rating)
                        reviewtitle = review.find('a', attrs={'data-hook':'review-title'})
                        if reviewtitle is None:
                            continue
                        reviewcontent.append(reviewtitle.text)
                        reviewbody = review.find('span', attrs={'data-hook':'review-body'})
                        if reviewbody is None:
                            continue
                        reviewcontent.append(reviewbody.find('span').text)
                        prodreviews.append(reviewcontent)
                    pagination = soup.find('ul', attrs = {"class":"a-pagination"})
                    if pagination is None:
                        break
                    nextbutton = pagination.find('li', attrs = {"class":"a-last"})
                    if nextbutton is None:
                        break
                    nexturlhtml = nextbutton.find('a')
                    if nexturlhtml is None:
                        break
                    nexturl = SITE + nexturlhtml.attrs['href']
                if len(prodreviews) > RvPP:
                    allreviews.extend(random.sample(prodreviews, RvPP))
                else:
                    allreviews.extend(prodreviews)
                print(len(allreviews))
                # Need to check if there's anything to save. Empty results pages process fast, overwriting could take a while.
                if len(allreviews) > savedreviews + 500:
                    savedreviews = len(allreviews)
                    print('Saving progress...')
                    with open('prodlist' + lang + '.pkl', "wb") as fp:
                        pickle.dump(prodlist, fp)
                        fp.close()
                    with open('reviews' + lang + '.pkl', "wb") as fp:
                        pickle.dump(allreviews, fp)
                        fp.close()
                    print('Done saving!')
    if len(allreviews) > savedreviews:
        savedreviews = len(allreviews)
        print('Saving final progress...')
        with open('prodlist' + lang + '.pkl', "wb") as fp:
            pickle.dump(prodlist, fp)
            fp.close()
        with open('reviews' + lang + '.pkl', "wb") as fp:
            pickle.dump(allreviews, fp)
            fp.close()
        print('Done saving!')
    print(len(allreviews))
    print(allreviews[0])
driver.close()