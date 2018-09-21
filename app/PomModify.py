import xml.etree.cElementTree as ET
from xml.etree.ElementTree import Element
from MavenPom import Pom, Dependency, Location
import copy

ET.register_namespace('', "http://maven.apache.org/POM/4.0.0")

prefix = '{http://maven.apache.org/POM/4.0.0}'
groupId_tag = 'groupId'
artifactId_tag = 'artifactId'
dependency_tag = 'dependency'
dependencies_tag = 'dependencies'
management_tag = 'dependencyManagement'
properties_tag = 'properties'
exclusion_tag = 'exclusion'
exclusions_tag = 'exclusions'
version_tag = 'version'
scope_tag = 'scope'


'''
解决冲突：
引用到的tc组件 在dependency management中有exclusion的依赖将依赖下移

处理的步骤：
1. 在dependency management中定义过但是从未被使用的
2. 在dependency management和dependencies中均有定义的
    只要有exclusion的都需要全部保留
    如果没有exclusion的 是继承自父类的或者import的组件要将dependency management中的依赖删除
3.只在下方有定义的在上方没定义的 全部删除版本号
    有exclusion 
        全部上移 
    没有exclusion 
        来自继承
            不需上移
        不来自继承
            上移

尽可能少的处理次数
'''


class PomModify:
    def __init__(self, target_pom, import_pom=None):
        self._target_pom = target_pom
        self._parent_pom = self._target_pom.parent.tree
        self._import_pom = import_pom

    def add_import_pom(self):
        element = self._target_pom.management_dict.get(self._import_pom.location)

        if element:
            version = element.find(prefix+version_tag)
            if version is not None:
                version.text = "${%s}" % (str(self._import_pom.location)+".version")

        else:
            dependency = Dependency(self._import_pom.location, "${%s}" % (str(self._import_pom.location)+".version"), 'pom', 'import')
            self._target_pom.management_dependencies.append(dependency.get_element())

        self.add_properties(str(self._import_pom.location) + ".version", self._import_pom.version)

    def add_properties(self, tag, text):
        """
        添加属性值
        :param:
        :return:
        """

        properties = self._target_pom.tree.find(prefix + properties_tag)
        common_tag = properties.find(prefix + tag)
        if common_tag is not None:

            common_tag.text = text
        else:
            common_node = self._create_node(tag, text)
            properties.append(common_node)

    def remove_unused(self):
        unnecessary = self._target_pom.management_dict.keys() - self._target_pom.dependencies_dict.keys()
        for key in unnecessary:
            if key == self._import_pom.location:
                continue
            ele = self._target_pom.management_dict.get(key)

            self._target_pom.management_dependencies.remove(ele)

    def move_duplicate(self):
        """
        重复部分
            来自继承：
                上方删除
                exclusion写在下方
            非继承
                exclusion写在上方
                下方exclusion删除
        :return:
        """
        # 如果是这两个的交集
        duplicate = self._target_pom.management_dict.keys() & self._target_pom.dependencies_dict.keys()
        for key in duplicate:
            management_element = self._target_pom.management_dict.get(key)
            dependency_element = self._target_pom.dependencies_dict.get(key)

            management_exclusions = management_element.find(prefix + exclusions_tag)
            dependency_exclusions = dependency_element.find(prefix + exclusions_tag)

            if self.is_form_parent(key):
                # 上下都有exclusion
                self._target_pom.management_dependencies.remove(management_element)
                if management_exclusions and dependency_exclusions:
                    exclusion_list = management_exclusions.findall(prefix + exclusion_tag)
                    for exclusion in exclusion_list:
                        dependency_exclusions.append(exclusion)
                    continue
                if management_exclusions:
                    dependency_element.append(management_exclusions)
                    continue

                self._remove_version(dependency_element)

            else:

                if dependency_exclusions:
                    dependency_element.remove(dependency_exclusions)

                    if management_exclusions:
                        exclusion_list = dependency_exclusions.findall(prefix+exclusion_tag)
                        for exclusion in exclusion_list:
                            management_exclusions.append(exclusion)
                    else:
                        management_element.append(dependency_exclusions)

    def move_single_to_management(self):
        """
        3.只在下方有定义的在上方没定义的 全部删除版本号
            有exclusion
                来自继承
                    下面部分删除版本号
                非来自继承
                    上移保留版本号
                    下面部分保留版本号
            没有exclusion
                来自继承
                    下面部分删除版本号
                不来自继承
                        上移保留版本号
                        下面部分删除版本号
        """
        up = self._target_pom.dependencies_dict.keys() - self._target_pom.management_dict.keys()

        for key in up:
            dependency_element = self._target_pom.dependencies_dict.get(key)
            exclusions = dependency_element.find(prefix + exclusions_tag)

            if not self.is_form_parent(key):
                self._target_pom.management_dependencies.append(copy.deepcopy(dependency_element))
                self._remove_version(dependency_element)
                if exclusions:
                    dependency_element.remove(exclusions)

    @staticmethod
    def _remove_version(dependency_element):
        version = dependency_element.find(prefix + version_tag)
        if version is not None:
            dependency_element.remove(version)

    def is_form_parent(self, location):
        return location in self._parent_pom.management_dict or location in self._import_pom.management_dict

    @staticmethod
    def _create_node(tag, text):
        element = Element(tag)
        element.text = text
        return element

    def write(self, path, encoding='utf-8'):
        self._target_pom.tree.write(path, encoding=encoding)


