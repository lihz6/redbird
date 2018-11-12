apil = (' ', '(', '(r)', ')', 'aɪ', 'aʊ', 'b', 'd', 'dʒ', 'e', 'eə', 'eɪ', 'f',
        'h', 'i', 'iː', 'j', 'juː', 'k', 'l', 'm', 'n', 'oʊ', 'p', 'r', 's',
        't', 'tʃ', 'u', 'uː', 'v', 'w', 'x', 'z', 'æ', 'ð', 'ŋ', 'ɑ', 'ɑː',
        'ɒ', 'ɔɪ', 'ɔː', 'ə', 'ər', 'əʊ', 'ɜː', 'ɡ', 'ɪ', 'ɪə', 'ʃ', 'ʊ', 'ʊə',
        'ʌ', 'ʒ', 'ˈ', 'ˌ', 'θ')


def _make_tran():
    key_1 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    key_2 = 'abcdefghijklmnopqrstuvwxyz'
    output = ''
    for api in apil:
        if len(api) > 1 or api in '()':
            char, *key_2 = key_2
            output += char
        else:
            char, *key_1 = key_1
            output += char
    return output


# assert tran == _make_tran
tran = 'AabcdeBCfDghEFGiHjIJKLkMNOPlQmRSTUVWXYnZop0qrs12t34u56789'


def find(api):
    high = len(apil) - 1
    low = 0
    while low <= high:
        mid = (low + high) >> 1
        if apil[mid] == api:
            return tran[mid], len(api)
        elif apil[mid] < api:
            low = mid + 1
        else:
            high = mid - 1
    if len(api) == 1:
        raise Exception('illegal char: ' + api)
    return find(api[:-1])


def encode(pron):
    s = 0
    output = ''
    while s < len(pron):
        char, step = find(pron[s:s + 3])
        output += char
        s += step

    return output

def decode(code):
    output = ''
    for b in code:
        output += apil[tran.index(b)]
    return output



def encase(pron):
    output = tran[(len(pron) - 1) % len(tran)]
    for b in encode(pron):
        output += '-' + b if b >= 'a' else b
    return output.upper()



def decase(code):
    code = code.upper()
    output = ''
    i = 1
    while i < len(code):
        b = code[i]
        if b == '-':
            i += 1
            b = code[i].lower()
        output += apil[tran.index(b)]
        i += 1
    return output
