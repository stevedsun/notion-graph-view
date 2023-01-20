__all__ = ["relation_logger"]

class __RelationLogger(object):
    def __init__(self):
        self._relations = []

    @property
    def relations(self):
        return self._relations

    def relationExists(self, parentId: str, childId: str):
        return self.getKey(parentId, childId) in self._relations

    def addRelation(self, parentId: str, childId: str):
        if(self.relationExists(parentId, childId)):
            pass
        
        self._relations.append(self.getKey(parentId, childId))

    @staticmethod   
    def getKey(parentId: str, childId: str):
        return parentId + "-" + childId


relationLogger = __RelationLogger()
