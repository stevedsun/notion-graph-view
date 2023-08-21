import re


def contains_mention_or_relation_type(obj_str: str) -> bool:
    '''Quickly parse if the json string contains relation or mention type block'''
    return re.search("'type': 'relation'", obj_str) != None or re.search("'type': 'mention'", obj_str) != None


def is_same_block_id(id_1, id_2: str) -> bool:
    formated_id_1 = id_1.replace("-", "")
    formated_id_2 = id_2.replace("-", "")
    return formated_id_1 == formated_id_2
