import re


def contains_mention_or_relation_type(obj_str: str) -> bool:
    '''Quickly parse if the json string contains relation or mention type block'''
    return re.search("'type': 'relation'", obj_str) or re.search("'type': 'mention'", obj_str)
