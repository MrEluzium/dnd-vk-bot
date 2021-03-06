#!/usr/bin/env python
from bs4 import BeautifulSoup as bs
import requests
from textwrap import fill as wrap

__all__ = ['Roll20', 'Roll20Monster', 'Roll20Spell', 'Roll20Item']


def stringify(text):
    text = text.replace('<br>', '\n').replace('<br />', '\n')
    text = text.replace('<h2>', '*').replace('</h2>', '*\n')
    text = text.replace('<strong>', '').replace('</strong>', '')
    return wrap(text, 80, drop_whitespace=False, replace_whitespace=False)


def score_to_mod(score):
    return '{:+d}'.format((score - 10) // 2)


class Roll20:

    def __init__(self, name, site='https://roll20.net/compendium/dnd5e/'):
        self.name = name.rstrip().title()
        formatted_name = self.name.replace(' ', '_')
        url = site + formatted_name
        page = requests.get(url)
        if page.status_code != 200:
            raise IOError('{:s} not found at {:s}.'.format(name,
                                                           url))
        if 'marketplace' in page.url:
            raise IOError('{:s} not found at {:s}, '
                          'likely because this content is behind a paywall. '
                          'Encourage developer to add alternative back-ends to Roll20'.format(name, url))
        html = page.text
        soup = bs(html, 'html.parser')
        self.attributes = ({stringify(a.text):
                                stringify(a.find_next(attrs={'class':
                                                                 'value'}).text)
                            for a in soup.find_all(attrs={'class':
                                                              'col-md-3 attrName'})})
        self.desc = '\n'.join([stringify(val.text)
                               for val in soup.find_all(id='origpagecontent',
                                                        attrs={'type':
                                                                   'text/html'})])

    def get(self, key, alt=None):
        if key == 'desc':
            return self.desc or alt
        else:
            return self.attributes.get(key, alt)

    @property
    def str_attributes(self):
        res = ""
        for k, v in self.attributes.items():
            res += k + ': ' + v + '\n'
        return res

    @property
    def str_desc(self):
        res = '\n\nDescription\n===========================\n' + self.desc
        return res

    def __len__(self):
        return len(self.attributes)

    def __str__(self):
        return self.name + '\n\n' + self.str_attributes + self.str_desc

    @property
    def as_unicode(self):
        return self.__str__().encode('utf-8')


class Roll20Monster(Roll20):

    def __init__(self, name,
                 site='https://roll20.net/compendium/dnd5e/Monsters:'):
        Roll20.__init__(self, name, site=site)

    @property
    def str_attributes(self):
        res = ''
        for k in ['HP', 'AC', 'Speed', 'Challenge Rating']:
            res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        res += '\n'
        for k in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            res += k + '\t'
        res += '\n'
        for k in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            s = self.get(k, None)
            res += '{:s} ({:s})\t'.format(s, score_to_mod(int(s)))
        res += '\n\n'
        for k in ['Type', 'Size', 'Alignment', 'Senses', 'Skills',
                  'Languages']:
            res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        return res


class Roll20Spell(Roll20):
    def __init__(self, name,
                 site='https://roll20.net/compendium/dnd5e/Spells:'):
        Roll20.__init__(self, name, site=site)

    @property
    def str_attributes(self):
        res = ''
        for k in ['Level', 'School', 'Classes']:
            if self.get(k) is not None:
                res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        res += '\n'
        for k in ['Casting Time', 'Duration', 'Concentration',
                  'Components', 'Material']:
            if self.get(k) is not None:
                res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        res += '\n'
        for k in ['Range', 'Damage', 'Damage Type', 'Save', 'Target']:
            if self.get(k) is not None:
                res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        return res


class Roll20Item(Roll20):
    def __init__(self, name,
                 site='https://roll20.net/compendium/dnd5e/Items:'):
        Roll20.__init__(self, name, site=site)


def main(text, Search_only=None):
    item = None
    if Search_only == "monster":
        item = Roll20Monster(text)
    elif Search_only == "spell":
        item = Roll20Spell(text)
    elif Search_only == "item":
        item = Roll20Item(text)
    else:
        for r in [Roll20Monster, Roll20Spell,
                  Roll20Item, Roll20]:
            try:
                item = r(text)
            except IOError as e:
                continue
            else:
                break
    if item is None or len(item) == 0:
        return 'Not Found'
    else:
        try:
            return item
        except UnicodeEncodeError:
            return item.as_unicode

