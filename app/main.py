from .PomModify import PomModify
from .MavenPom import Pom
from .config import tc_pom_url, common_version

# 需要重写的pom文件的路径
file_path = 'C:\\Users\\junrong.chen\\IdeaProjects\\{}\\pom.xml'.format('booth_svr')


def run():
    # 根据url生成pom对象
    tc_pom = Pom.from_url(tc_pom_url)
    # 根据文件路径生成pom对象
    target_pom = Pom.from_file(file_path)
    # 传入要修改的pom和需要引入的pom
    modify = PomModify(target_pom, import_pom=tc_pom)
    # 在dependencyManagement中增加需要导入的依赖
    modify.add_import_pom()
    # 在properties中增加对应属性
    modify.add_properties('qunar.common.version', common_version)
    # 移除不需要使用的依赖  可以注释这条方法或者手动解决依赖冲突
    modify.remove_unused()
    # 处理management中的重复部分
    modify.move_duplicate()
    # 将dependency中单独定义的依赖交由management管理
    modify.move_single_to_management()
    # 生成新的pom的地址  默认写会原文件
    modify.write(file_path)
