import spacy
import en_core_web_sm
nlp = en_core_web_sm.load()
base = None

INTRODUCTION = '''
    Please enter statements and queries. Don't forget to put question mark ('?') after the query.
    Enter 'quit' (without quotes) in order to stop the program.
    To see knowledge base after each entry enter start. To turn it off enter stop. By default it is disabled.
'''

SHELL_SIGN = '> '
UNKNOWN = 'No information'
UNKNOWN_QUERY = 'Unknown query format'

ENDING = '''
    The program finished. Thank you!
'''


def getRoot(tokens):
    for token in tokens:
        if token.dep_ == 'ROOT':
            return token
    return None


def getNegation(tokens, root):
    neg = False
    for token in tokens:
        if token.dep_ == 'neg' and token.head.text == root.text:
            neg = not neg
    return neg


def findSubject(tokens, root):
    for token in tokens:
        if token.dep_ == 'nsubj' and token.head.text == root.text:
            return token
    return None


def findPreposition(tokens, root):
    for token in tokens:
        if token.dep_ == 'prep' and token.head.text == root.text:
            return token
    return None


def findObject(tokens, root, p=False):
    if root is None:
        return None
    txt = 'pobj' if p else 'dobj'

    for token in tokens:
        if token.dep_ == txt and token.head.text == root.text:
            return token
    return None


def findAttribute(tokens, root):
    attributes = {'attr', 'acomp'}
    for token in tokens:
        if token.dep_ in attributes and token.head.text == root.text:
            return token
    return None


def findAuxilary(tokens, root):
    for token in tokens:
        if token.dep_ == 'aux' and token.head.text == root.text:
            return token
    return None


def findCompounds(tokens, subject):
    res = []
    for token in tokens:
        if token.dep_ == 'compound' and token.head.text == subject.text:
            res.append(token)
    return res


def add_to_base(s, a, b, neg=False):
    if s in base:
        base[s].append((a, b, neg))
    else:
        base[s] = [(a, b, neg)]


def processStatement(line):
    a = nlp(line)
    # for token in a:
    #     print("Word = {}, Lemma = {}, PoS/Tag = {}/{}, Role = {} to [{}]".format(
    #         token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.text))
    root = getRoot(a)
    subject = findSubject(a, root)
    sll = subject.text.lower()
    neg = getNegation(a, root)
    compounds = findCompounds(a, subject)

    for comp in compounds:
        add_to_base(sll, 'be', comp.lemma_.lower())

    if root.lemma_.lower() == 'be':
        attr = findAttribute(a, root)
        add_to_base(sll, 'be', attr.text.lower(), neg=neg)

    elif root.lemma_.lower() == 'own':
        prep = findPreposition(a, root)
        obj = findObject(a, prep, p=True)
        if obj is not None:
            add_to_base(sll, 'have', obj.text.lower(), neg)
        obj = findObject(a, root, p=False)
        if obj is not None:
            add_to_base(sll, 'have', obj.text.lower(), neg)

    else:
        prep = findPreposition(a, root)
        obj = findObject(a, prep, p=True)
        if obj is not None:
            add_to_base(sll, root.lemma_.lower(), obj.text.lower(), neg)
        obj = findObject(a, root, p=False)
        if obj is not None:
            add_to_base(sll, root.lemma_.lower(), obj.text.lower(), neg)


def findWhoAnswer(verb, obj, neg):
    res = []
    for name in base:
        for t in base[name]:
            if t[0] == verb and t[1] == obj.text.lower() and t[2] == neg:
                res.append(name)
    if len(res) == 0:
        return 'No one'

    ans = ''
    for name in set(res):
        ans += f'{name}, '
    return ans[:-2]


def processQuery(line):
    a = nlp(line)
    # for token in a:
    #     print("Word = {}, Lemma = {}, PoS/Tag = {}/{}, Role = {} to [{}]".format(
    #         token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.text))

    root = getRoot(a)
    subject = findSubject(a, root)
    sll = subject.text.lower()
    neg = getNegation(a, root)

    verb = root.lemma_.lower()
    if verb == 'own':
        verb = 'have'

    if subject.lemma_.lower() == 'who':
        attr = findAttribute(a, root)
        if attr is not None:
            return findWhoAnswer(verb, attr, neg)

        prep = findPreposition(a, root)
        obj = findObject(a, prep, p=True)
        if obj is not None:
            return findWhoAnswer(verb, obj, neg)
        else:
            obj = findObject(a, root)
            return findWhoAnswer(verb, obj, neg) if obj is not None else UNKNOWN_QUERY

    if root.lemma_.lower() == 'be':
        attr = findAttribute(a, root)
        if sll not in base:
            return UNKNOWN
        for t in base[sll]:
            if t[0] == 'be' and t[1] == attr.text.lower():
                return 'Yes' if neg == t[2] else 'No'
        return UNKNOWN

    dobj = findObject(a, root)
    aux = findAuxilary(a, root)
    if dobj.lemma_.lower() == 'what' and aux.lemma_.lower() == 'do':
        if sll not in base:
            return UNKNOWN

        res = []
        for t in base[sll]:
            if t[0] == verb and t[2] == neg:
                res.append(t[1])
        if len(res) == 0:
            return UNKNOWN
        else:
            ans = ''
            for t in set(res):
                ans += f'{t}, '
            return ans[:-2]
    else:
        return UNKNOWN_QUERY


def getFormatted(values):
    total = ''
    for value in values:
        current = f'[{value[0]}, {value[1]}, neg={value[2]}], '
        total += current
    return total[:-2] if len(total) > 0 else total


def printCurrentBase():
    print(len(base))
    for (item, value) in base.items():
        t = getFormatted(value)
        currentLine = f'[{item} - {t}]'
        print(currentLine)


if __name__ == '__main__':
    base = {}
    showBase = False
    print(INTRODUCTION)
    while True:
        line = input(SHELL_SIGN).strip()
        if line.strip().lower() == 'quit':
            break

        if line.strip().lower() == 'start':
            showBase = True
            printCurrentBase()
            continue

        if line.strip().lower() == 'stop':
            showBase = False
            continue

        if line[len(line) - 1] == '?':
            print(f'   {processQuery(line)}')
        else:
            processStatement(line)

        if showBase:
            printCurrentBase()

    print(ENDING)
