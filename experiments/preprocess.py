import pickle
import json
import io
import random

# This file takes the raw (pickled) output of the scraper and processes it to be suitable for the classifier.
LANGS = ['EN', 'JP', 'TR', 'DE']
RvPL = 10000 # Desired number of reviews per language to output. Each input language should always have more than this.
for lang in LANGS:
    arr = []
    fp = open("reviews" + lang + ".pkl", "rb")
    arr = pickle.load(fp)
    fp.close()
    # Review Content format = [category, name, rating, title, text]
    reviewbyrating = [[],[],[],[],[]]
    ratinghist = [0, 0, 0, 0, 0]
    categoryhist = {}
    for content in arr:
        r = content[2]-1
        ratinghist[r] += 1
        reviewbyrating[r].append(content)
        category = content[0]
        if category in categoryhist.keys():
            categoryhist[category] += 1
        else:
            categoryhist[category] = 1
    print(ratinghist)
    ratinghist2 = [0, 0, 0, 0, 0]
    for i in range(0, len(ratinghist)):
        ratinghist2[i] = len(reviewbyrating[i])
    print(ratinghist2)
    print(categoryhist)

    # Divide reviews into chunks as close to equal in size as possible. Need :target: reviews total
    # Algorithm: attempt to limit size of each chunk to equal sizes. If a chunk is smaller than the limit, start over with the new
    # Finally, integerize, distributing all the fractions
    keep = ratinghist.copy()
    dropped = [False, False, False, False, False]
    target = RVPL
    w = len(ratinghist)
    print(target/w)
    histsum = 0
    while histsum < target:
        histsum = 0
        droppedsum = 0
        neww = w
        for i in range(0, len(ratinghist)):
            if ratinghist[i] >= target / w:
                keep[i] = target/w
                histsum += target/w
            elif not dropped[i]:
                droppedsum += ratinghist[i]
                keep[i] = ratinghist[i]
                neww -= 1
                dropped[i] = True
        w = neww
        target -= droppedsum
    
    for i in range(0, len(keep)):
        keep[i] = int(keep[i])
    off = RVPL - sum(keep)
    for i in range(0, len(keep)):
        if off > 0 and ratinghist[i] > keep[i] + 1:
            keep[i] += 1
            off -= 1
    print(keep)
    print(sum(keep))
    arr = []
    for i in range(0, len(keep)):
        if ratinghist[i] > keep[i]:
            arr.extend(random.sample(reviewbyrating[i], keep[i]))
        else:
            arr.extend(reviewbyrating[i])
    print(len(arr))
    newarr = []
    # Format for TabularDataset
    for content in arr:
        newarr.append({"rating": content[2], "review": (content[3] + '<body>\n' + content[4])})
    if True:
        with io.open("reviews" + lang + ".json", "a", encoding="utf8") as f:
            
            print(json.dumps(newarr[0]))

            for i in newarr:
                f.write(json.dumps(i) + "\n")

            f.close()