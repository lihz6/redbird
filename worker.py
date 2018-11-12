from sqlite3 import connect
from threading import RLock
from derive import derive

############################################################

database = connect('vocab.db', check_same_thread=False)
cursor = database.cursor()
lock = RLock()

############################################################


def _quote(word): return word.replace("'", "''")


############################################################


def _history(search):
    def decorator(text, uuid):
        with lock:
            result = search(text, uuid)
            freq = 1 if result else 0
            sql = "INSERT INTO hist_tab VALUES('%s', '%s', %d, strftime('%%s','now'))"
            cursor.execute(sql % (uuid, _quote(text), freq))
            return result
    return decorator


############################################################


def _mean(word, mark, uuid):
    sql = "SELECT mean FROM mean_tab WHERE word = '%s' AND mark = '%s' AND uuid IN('', '%s') ORDER BY time DESC LIMIT 1"
    cursor.execute(sql % (_quote(word), mark, uuid))
    one = cursor.fetchone()
    if not one:
        return ''
    mean = one[0]
    if mean.startswith('@'):
        pair = mean[1:].split('@', 1)
        # `@word@mark`, `@mark` is optional
        pair.append(mark)
        return _mean(pair[0], pair[1], uuid)
    return mean


############################################################


def _pinvd(where, uuid):
    sql = "SELECT word, mark, pinv FROM pinv_tab WHERE word IN('%s')"
    # assert: "'" quoted in where
    cursor.execute(sql % where)
    pinvd = {}
    for word, mark, pinv in cursor.fetchall():
        data = [pinv, _mean(word, mark, uuid)]
        if word not in pinvd:
            pinvd[word] = {mark: data}
        else:
            pinvd[word][mark] = data
    return pinvd


@_history
def search_zh(text, uuid):
    words = [text[:e] for e in range(len(text), 0, -1)]
    where = "', '".join(_quote(w) for w in words)
    pinvd = _pinvd(where, uuid)
    return [{
        'word': word,
        'data': pinvd[word]
    } for word in words if word in pinvd]

############################################################


def _prond(where, uuid):
    sql = "SELECT word, mark, pronuk, pronus FROM pron_tab WHERE word COLLATE NOCASE IN('%s')"
    cursor.execute(sql % where)
    prond = {}
    for word, mark, pronuk, pronus in cursor.fetchall():
        data = [pronuk, pronus, _mean(word, mark, uuid)]
        if word not in prond:
            prond[word] = {mark: data}
        else:
            prond[word][mark] = data
    return prond


def _search_en(words, uuid):
    where = "', '".join(_quote(w) for w in words)
    prond = _prond(where, uuid)
    return [{
        'word': word,
        'data': prond[word]
    } for word in words if word in prond]


@_history
def search_en(text, uuid):
    for words in derive(text):
        items = _search_en(words, uuid)
        if items:
            return items
    return []


############################################################


def _mean_ok(word, mark, uuid, mean, link=None):
    if link == None:
        link = {(word, mark)}
    if not mean.startswith('@'):
        return mean
    if mean == '@':
        return False
    ms = mean[1:].split('@', 1)
    if len(ms) < 2:
        ms.append(mark)
    word, mark = ms
    if "'" in mark or (word, mark) in link:
        return False
    link.add((word, mark))
    sql = "SELECT mean FROM mean_tab WHERE word = '%s' AND mark = '%s' AND uuid IN('', '%s') ORDER BY time DESC LIMIT 1"
    cursor.execute(sql % (_quote(word), mark, uuid))
    one = cursor.fetchone()
    return one and _mean_ok(word, mark, uuid, one[0], link)


def define(word, data, uuid):
    with lock:
        changed = False
        for mark, mean in data.items():
            if "'" in mark or not _mean_ok(word, mark, uuid, mean):
                continue
            sql = "INSERT INTO mean_tab VALUES('%s', '%s', '%s', '%s', strftime('%%s','now'))"
            args = _quote(word), mark, uuid, _quote(mean)
            cursor.execute(sql % args)
            changed = True
        if changed:
            database.commit()
            return '1'
        return '0'

############################################################


def hintme(username):
    with lock:
        sql = "SELECT passhint FROM user_tab WHERE username = '%s'"
        cursor.execute(sql % username)
        one = cursor.fetchone()
        return one and one[0]

############################################################


def signin(username, password, oldid):
    with lock:
        sql = "SELECT useruuid FROM user_tab WHERE username = '%s' AND password = '%s'"
        cursor.execute(sql % (username, _quote(password)))
        one = cursor.fetchone()
        if not one:
            return None
        newid = one[0]
        sql = "UPDATE hist_tab SET uuid = '%s' WHERE uuid = '%s'"
        cursor.execute(sql % (newid, oldid))
        database.commit()
        return newid

############################################################


def signup(name, word, hint, uuid, gender, birday):
    with lock:
        sql = "INSERT OR IGNORE INTO user_tab VALUES('%s', '%s', '%s', '%s', %d, %d)"
        data = name, _quote(word), _quote(hint), uuid, gender, birday
        cursor.execute(sql % data)
        database.commit()

############################################################


def mynote(uuid, note, furl):
    from urllib.request import quote
    with lock:
        sql = "INSERT INTO note_tab VALUES('%s', '%s', '%s', strftime('%%s','now'))"
        data = uuid, _quote(note), quote(furl)
        print(sql % data)
        cursor.execute(sql % data)
        database.commit()
