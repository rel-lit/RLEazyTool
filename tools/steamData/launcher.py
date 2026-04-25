"""
启动器 - 检测虚拟环境、安装依赖并启动主程序
"""
import os
import sys
import subprocess


def print_separator():
    """打印分隔线"""
    print("=" * 60)


def check_virtualenv():
    """检查并激活虚拟环境"""
    print_separator()
    print("  正在检查Python环境...")
    print_separator()
    
    # 获取项目根目录（向上两级）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    venv_activate = os.path.join(project_root, ".venv", "Scripts", "activate.bat")
    
    if os.path.exists(venv_activate):
        print("[提示] 检测到虚拟环境，正在激活...")
        # 注意：在Python中无法真正"激活"虚拟环境
        # 但可以检查是否在虚拟环境中运行
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("[成功] 已在虚拟环境中运行")
        else:
            print("[警告] 虚拟环境存在但未激活，建议使用以下命令激活：")
            print(f"        cd {project_root}")
            print(f"        .venv\\Scripts\\activate")
    else:
        print("[警告] 未检测到虚拟环境，将使用系统Python")
    
    print()


def check_python():
    """检查Python版本"""
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 6):
            print("[错误] Python版本过低，需要Python 3.6+")
            print(f"       当前版本: {sys.version}")
            input("\n按任意键退出...")
            sys.exit(1)
        print(f"[成功] Python环境正常 (版本: {version.major}.{version.minor}.{version.micro})")
    except Exception as e:
        print(f"[错误] 无法检测Python版本: {e}")
        input("\n按任意键退出...")
        sys.exit(1)
    
    print()


def check_dependencies():
    """检查并安装依赖"""
    print_separator()
    print("  正在检查依赖库...")
    print_separator()
    
    required_modules = ['requests', 'bs4', 'openpyxl', 'PIL']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"[提示] 检测到缺少依赖库: {', '.join(missing_modules)}")
        print("[提示] 正在自动安装...")
        print()
        
        try:
            # 使用subprocess调用pip安装
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                print("[成功] 依赖安装完成")
            else:
                print("[错误] 依赖安装失败")
                print(result.stderr)
                print("\n请手动运行: pip install -r requirements.txt")
                input("\n按任意键退出...")
                sys.exit(1)
        except Exception as e:
            print(f"[错误] 安装过程出错: {e}")
            print("\n请手动运行: pip install -r requirements.txt")
            input("\n按任意键退出...")
            sys.exit(1)
    else:
        print("[成功] 所有依赖库已安装")
    
    print()


def start_main_program():
    """启动主程序"""
    print_separator()
    print("  启动程序...")
    print_separator()
    print()
    
    # 导入并运行主程序
    try:
        import main
        main.main()
    except Exception as e:
        print(f"\n[错误] 程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        input("\n按任意键退出...")
        sys.exit(1)


def main():
    """主函数"""
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 执行启动流程
    check_virtualenv()
    check_python()
    check_dependencies()
    start_main_program()


if __name__ == '__main__':
    main()
