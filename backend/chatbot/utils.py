from bs4 import BeautifulSoup

class Document_:
    def __init__(self, metadata, page_content):
        self.metadata = metadata
        self.page_content = page_content

def extract_content_chunks_from_file(html_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    docs = []

    h4_tags = soup.find_all('h4')

    for h4 in h4_tags:
        metadata = h4.get_text(strip=True)
        page_content = ''
        next_element = h4.next_element

        while next_element:
            if next_element.name == 'h4':
                break

            if next_element.name == 'span':
                text = next_element.get_text(" ", strip=True)
                if text not in page_content:
                    page_content += text + ' '

            elif next_element.name == 'li':
                li_text = next_element.get_text(" ", strip=True)
                if li_text not in page_content:
                    page_content = page_content.rstrip() + '\n' + li_text + ' '

            next_element = next_element.next_element

        page_content = page_content.strip()
        docs.append(Document_(metadata, page_content))

    return docs

""" if __name__ == '__main__':
    html_file_path = 'html/paca.html'
    docs = extract_content_chunks_from_file(html_file_path)

    for doc in docs:
        print(doc.page_content)
        print('---') """