#-*- coding: utf-8 -*-
import urllib
import re
import argparse
from workflow import Workflow
import sys
# reload(sys)
# sys.setdefaultencoding('euc-kr')


class HtmlParser(object):
    def __init__(self, **kwargs):
        self.base_url = kwargs.get('base_url', '')
        self.url = kwargs.get('url', '')
        self.pattern = kwargs.get('pattern', '')

    """
    decoding is not necessary if default encoding is euc-kr
    however, use my decoding function in the case of utf-8
    """
    @staticmethod
    def decode(text):
        ret = text
        try:
            ret = text.decode('euc-kr')
        except:
            pass
        try:
            ret = text.decode('cp949')
        except:
            pass
        try:
            ret = text.decode('utf-8')
        except:
            pass
        return ret

    @staticmethod
    def decode_rec(obj):
        if isinstance(obj, list):
            return [HtmlParser.decode_rec(element) for element in obj]
        elif isinstance(obj, dict):
            return {HtmlParser.decode_rec(key): HtmlParser.decode_rec(value) for key, value in obj}
        elif isinstance(obj, set):
            return {HtmlParser.decode_rec(element) for element in obj}
        elif isinstance(obj, tuple):
            return tuple(HtmlParser.decode_rec(element) for element in obj)
        else:
            return HtmlParser.decode(obj)

    def read(self):
        return urllib.urlopen(self.url).read()

    def findall(self):
        html_page = self.read()
        regex = re.compile(self.pattern)
        find_pairs = regex.findall(html_page)
        decoded_pairs = HtmlParser.decode_rec(find_pairs)
        return decoded_pairs


class PpomppuParser(HtmlParser):
    def __init__(self, **kwargs):
        super(PpomppuParser, self).__init__(**kwargs)
        self.img_pattern = r'''<img.*?src\s*=\s*["'](.+?)["'].*?>'''

    def parse_title(self, title):
        match = re.search(self.img_pattern, title)
        if match:
            icon = match.groups()[0].rsplit('/', 1)[-1]
            title = re.sub(self.img_pattern, '', title)
            return icon, title
        return 'icon.png', title

    def get_items(self):
        items = []
        for link, title, comment, timestamp, like, view in self.findall():
            icon, title = self.parse_title(title)
            item = dict(arg=self.base_url + link,
                        valid=True,
                        icon=icon,
                        title=title,
                        subtitle=u'{timestamp}  댓글: {comment}, 추천: {like}, 조회: {view}'.format(timestamp=timestamp, comment=comment, like=like, view=view),
                        modifier_subtitles={
                            u'cmd': u'주소를 클립보드에 저장합니다.'
                        }
                        )
            items.append(item)
        return items


def main(wf):
    """
    Example:
        <a href="view.php?id=ppomppu&page=1&divpage=46&no=263644"  >
        <font class=list_title> TITLE </font></a>&nbsp;<span class=list_comment2>
        <span style='cursor:pointer;' onclick='win_comment("popup_comment.php?id=ppomppu&no=263644");'>8</span> </span></td></tr></table></td>
        <td nowrap class='eng list_vspace' colspan=2  title="17.02.15 14:05:21" ><nobr class='eng list_vspace'>14:05:21</td>
        <td nowrap class='eng list_vspace' colspan=2>4 - 0</td>
        <td nowrap class='eng list_vspace' colspan=2>1415</td></tr>
    """
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('--page', '-p', help='page number', nargs='*', required=False)
    argument_parser.add_argument('--type', '-t', help='board type', required=False, type=int)
    args = argument_parser.parse_args()
    args.page.insert(0, '1')
    ppompu_parser = PpomppuParser(base_url='http://www.ppomppu.co.kr/zboard/',
                                url='http://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu%s&page=%s' % (args.type or '', args.page[-1]),
                                pattern=r"""<a.*?href\s*=\s*["'](.+?)["'].*?>.*?<font.*?class\s*=\s*list_title.*?>(.+?)</font>.*?onclick\s*=\s*'win_comment.*?'>(.*?)</span>[^.]*?title\s*=\s*["'](.+?)["'].*?>.*?colspan=2>(.*?)</td>.*?colspan=2>(.*?)</td>""")
    for item in ppompu_parser.get_items():
        wf.add_item(**item)
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
