from bs4 import BeautifulSoup
from pathlib import Path
import json
from enum import Enum

# soup = BeautifulSoup(html_doc, 'html.parser')
SPLIT_TAGS = '<td class="xl7921221">&nbsp;</td>'
# SPLIT_TAGS = ['<td class="xl7221221"> </td>', '"<td class=\"xl7921221\"> </td>"']
SPLIT_TAGS_CLASS_BEFORE = ["xl8121221"]
# SPLIT_TAGS_VALUE_BEFORE = [" ", "\xa0", "мин."]
SPLIT_TAGS_VALUE_BEFORE = ["мин."]
SPLIT_TAGS_CLASS_AFTER = ["xl7221221", "xl7921221", "xl8021221"]
SPLIT_TAGS_VALUE_AFTER = [" ", "\xa0"]
CURRENT_TR_ID = 0

EMPTY_TDS = {
    "td1": [
        '<td colspan="46" class="xl6621221">&nbsp;</td>',
        '<td class="xl6621221"></td>',
    ],
    "td2": [
        '<td class="xl7221221">&nbsp;</td>',
        '<td colspan="70" class="xl6621221"></td>',
        '<td class="xl6621221"></td>',
    ],
    "td3": [
        '<td class="xl7221221">&nbsp;</td>',
        '<td colspan="67" class="xl6621221"></td>',
    ],
}


HTML_IN_FILE_NAME = "table_in.html"
HTML_TEMPLATE_FILE_NAME = "table_templates.html"
HTML_OUT_FILE_NAME = "table_out.html"
JSON_OUT_FILE_NAME = "table_out.json"


def load_html(file_name) -> BeautifulSoup:
    html_path = Path(__file__).parents[1] / "tables" / file_name
    with open(html_path, "r") as f:
        contents = f.read()

    _soup = BeautifulSoup(contents, "html.parser")

    table = _soup.find("table")
    if table is None:
        raise Exception("BeautifulSoup cannot find table")

    return _soup


def load_json(file_name) -> BeautifulSoup:
    html_path = Path(__file__).parents[1] / "tables" / file_name
    with open(html_path, "r") as f:
        js_content = json.load(f)
    return js_content


def dict_to_json(dict):
    file_path = Path(__file__).parents[1] / "tables" / JSON_OUT_FILE_NAME
    with open(file_path, "w", encoding="utf8") as f:
        f.write(json.dumps(dict, ensure_ascii=False, indent=4, sort_keys=True))


def soup_to_file(soup):
    file_path = Path(__file__).parents[1] / "tables" / HTML_OUT_FILE_NAME
    with open(file_path, "w", encoding="utf8") as f:
        f.write(str(soup))


def check_split(column, td, classes=None, values=None, do_check_style=False) -> int:
    """
    Вычисляет есть ли "разделение" и нужно ли считать что мы в новом столбце

    Return:
        column:int - Номер колонки
    """
    if column > 1:
        return column

    # Подходит по классу
    if classes is None:
        classy = True
    else:
        classy = set(td.get("class")).intersection(classes)

    # Подходит по значению
    if values is None:
        qualify = True
    else:
        qualify = td.string in values

    # Подходит по стилю
    if not do_check_style:
        style = True
    else:
        style = td.get("style") is not None

    # Проверка и прибавление колонки
    if classy and qualify and style:
        column += 1

    return column


def fetch_td_from_tr(tr) -> list:
    tds = tr.find_all("td")
    column = 0

    splits = [[], [], []]

    for td in tds:
        column = check_split(column, td, SPLIT_TAGS_CLASS_AFTER, SPLIT_TAGS_VALUE_AFTER)
        splits[column].append(str(td))
        column = check_split(
            column,
            td,
            SPLIT_TAGS_CLASS_BEFORE,
            SPLIT_TAGS_VALUE_BEFORE,
            do_check_style=True,
        )
    return splits


def table_to_json(soup):
    global CURRENT_TR_ID
    table = soup.find("table")
    table_json = {
        "tr": [],
        "td1": [],
        "td2": [],
        "td3": [],
    }
    table_rows = table.find_all("tr")
    print(f"Len ROWS: {len(table_rows)}")
    # for tr in table_rows:
    for tr_idx, tr in enumerate(table_rows):
        CURRENT_TR_ID = tr_idx
        
        table_json["tr"].append(tr.attrs)
        tds = fetch_td_from_tr(tr)
        table_json["td1"].append(tds[0])
        table_json["td2"].append(tds[1])
        table_json["td3"].append(tds[2])
    print(f'Len TD1: {len(table_json["td1"])}')
    print(f'Len TD2: {len(table_json["td2"])}')
    print(f'Len TD3: {len(table_json["td3"])}')

    return table_json


def get_element_from_content(
    json_content: dict,
    td_number: str,
    element_number: int,
) -> list:
    # return json_content[key]
    try:
        _obj = json_content[td_number][element_number]
    except IndexError:
        # _obj = EMPTY_TDS[td_number]
        _obj = []
    return _obj


def json_to_table(soup: BeautifulSoup, json_content: dict) -> BeautifulSoup:
    table = soup.find("table")
    tbody = table.find("tbody")
    tbody.decompose()

    new_tbody = soup.new_tag("tbody")
    for i in range(len(json_content["tr"])):
        _tr = soup.new_tag("tr")
        _tr.attrs = json_content["tr"][i]
        tds = (
            get_element_from_content(json_content, "td1", i)
            + get_element_from_content(json_content, "td2", i)
            + get_element_from_content(json_content, "td3", i)
        )
        tds_str = "\n".join(tds)
        _tr.append(BeautifulSoup(tds_str, "html.parser"))
        new_tbody.append(_tr)
        table.append(new_tbody)
    return soup


def html_to_json():
    soup = load_html(HTML_IN_FILE_NAME)
    json = table_to_json(soup)
    dict_to_json(json)


def json_to_html():
    soup = load_html(HTML_IN_FILE_NAME)
    json_content = load_json(JSON_OUT_FILE_NAME)
    new_soup = json_to_table(soup, json_content)
    soup_to_file(new_soup)


def check_quality():
    soup1 = load_html(HTML_IN_FILE_NAME)
    soup2 = load_html(HTML_OUT_FILE_NAME)

    t1 = soup1.find("table").find_all("tr")
    t2 = soup2.find("table").find_all("tr")

    print(f"Len t1: {len(t1)}, Len t2: {len(t2)}")
    arr1 = []
    arr2 = []
    for i in range(len(t1)):
        arr1.append(len(t1[i].find_all("td")))
        arr2.append(len(t2[i].find_all("td")))
    print(f"Len arr1: {len(arr1)}, Len arr2: {len(arr2)}")
    print(f"Arr1 == Arr2: {arr1 == arr2}")
    print(f"Arr1: {arr1}")
    print(f"Arr2: {arr2}")


def main():
    # html_to_json()
    json_to_html()
    check_quality()


if __name__ == "__main__":
    main()
