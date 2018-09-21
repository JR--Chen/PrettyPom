import xml.etree.cElementTree as ET
from xml.etree.ElementTree import Element
from TreeBuilder import CommentedTreeBuilder
from config import maven_url, common_version
import requests

ET.register_namespace('', "http://maven.apache.org/POM/4.0.0")
prefix = '{http://maven.apache.org/POM/4.0.0}'
groupId_tag = 'groupId'
artifactId_tag = 'artifactId'
dependency_tag = 'dependency'
dependencies_tag = 'dependencies'
management_tag = 'dependencyManagement'
properties_tag = 'properties'
exclusions_tag = 'exclusions'
exclusion_tag = 'exclusion'
version_tag = 'version'
parent_tag = 'parent'
scope_tag = 'scope'


class Pom:
    parser = ET.XMLParser(target=CommentedTreeBuilder())

    def __init__(self, tree, path=None):
        self.tree = tree
        self._dependency_dict = {}
        self._parent = self.tree.find(prefix + parent_tag)
        self.dependencies = self.tree.find(prefix + dependencies_tag)
        self.management = self.tree.find(prefix + management_tag)
        self._version = self.tree.find(prefix + version_tag)
        self.management_dependencies = self.management.find(prefix + dependencies_tag)
        self._artifactId = self.tree.find(prefix + artifactId_tag)
        self._groupId = self.tree.find(prefix + groupId_tag)
        self.location = Location(self.groupId, self.artifactId)

    @classmethod
    def from_file(cls, filename):
        tree = ET.parse(filename, cls.parser)
        return cls(tree)

    @classmethod
    def from_url(cls, url):
        result = requests.get(url)
        tree = ET.fromstring(result.content)
        return cls(tree)

    @property
    def dependencies_dict(self):
        dependencies_dict = dict()
        if not self.dependencies:
            return
        dependency_list = self.dependencies.findall(prefix + dependency_tag)
        for dependency in dependency_list:
            artifactId = dependency.find(prefix + artifactId_tag).text
            groupId = dependency.find(prefix + groupId_tag).text
            dependencies_dict[Location(groupId, artifactId)] = dependency

        return dependencies_dict

    @property
    def management_dict(self, need_scope=False):
        management_dict = dict()
        if not self.management:
            return
        dependency_list = self.management_dependencies.findall(prefix + dependency_tag)
        for dependency in dependency_list:
            if not need_scope:
                scope = dependency.find(prefix + scope_tag)
                if scope is None or (scope.text != 'runtime'):
                    artifactId = dependency.find(prefix+artifactId_tag).text
                    groupId = dependency.find(prefix+groupId_tag).text
                    management_dict[Location(groupId, artifactId)] = dependency

        return management_dict

    @property
    def version(self):
        if self._version is not None:
            return self._version.text
        else:
            return None

    @property
    def groupId(self):
        if self._groupId is not None:
            return self._groupId.text
        else:
            return None

    @property
    def artifactId(self):
        if self._artifactId is not None:
            return self._artifactId.text
        else:
            return None

    @property
    def parent(self):
        if self._parent is not None:
            group = self._parent.find(prefix+groupId_tag).text
            artifact = self._parent.find(prefix + artifactId_tag).text
            version = self._parent.find(prefix + version_tag).text
            return Dependency(Location(group, artifact), version)


class Dependency:
    def __init__(self, location, version, typ=None, scope=None):
        self._location = location
        self._version = version
        self._type = typ
        self._scope = scope

    def __str__(self):
        return str(self._location)+':'+self._version

    def get_element(self):
        dependency = self._create_node("dependency")
        if self._location:
            dependency.append(self._create_node("groupId", self._location.groupId))
            dependency.append(self._create_node("artifactId", self._location.artifactId))
        if self._version:
            dependency.append(self._create_node("version", self._version))
        if self._type:
            dependency.append(self._create_node("type", self._type))
        if self._scope:
            dependency.append(self._create_node("scope", self._scope))

        return dependency

    @staticmethod
    def _create_node(tag, text=None):
        element = Element(tag)
        element.text = text
        return element

    @property
    def tree(self):
        return Pom.from_url(self.url)

    @property
    def url(self):
        group_url = self._location.groupId.replace('.', "/")
        path = maven_url+'/'+group_url+'/'+self._location.artifactId+'/'+self._version+'/'
        return path+self.file_name

    @property
    def file_name(self):
        return self._location.artifactId + '-' + self._version + '.pom'


class Location:
    def __init__(self, groupId, artifactId):
        self._groupId = groupId
        self._artifactId = artifactId

    def __hash__(self):
        return hash(self._artifactId + self._groupId)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        return "{}.{}".format(self._groupId, self._artifactId)

    def __repr__(self):
        return self.__str__()

    @property
    def groupId(self):
        return self._groupId

    @property
    def artifactId(self):
        return self._artifactId
