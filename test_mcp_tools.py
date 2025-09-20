#!/usr/bin/env python3
"""
Полноценный тест для проверки доступности ADF инструментов в MCP
"""
import asyncio
import json
import sys
from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class Colors:
    """Цвета для вывода в терминал"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str) -> None:
    """Печатает заголовок"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text: str) -> None:
    """Печатает успешное сообщение"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Печатает сообщение об ошибке"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text: str) -> None:
    """Печатает информационное сообщение"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Печатает предупреждение"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

async def test_mcp_connection() -> List[Any]:
    """Тестирует соединение с MCP сервером и возвращает список инструментов"""
    print_header("ТЕСТИРОВАНИЕ MCP СОЕДИНЕНИЯ")
    
    try:
        print_info("Запускаем MCP сервер...")
        
        # Настройки для запуска MCP сервера
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "mcp-atlassian", "--env-file", ".env"],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print_success("Соединение с MCP сервером установлено")
                
                # Инициализируем сессию
                await session.initialize()
                print_success("MCP сессия инициализирована")
                
                # Получаем список инструментов
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print_success(f"Получено {len(tools)} инструментов от MCP сервера")
                return tools
                
    except Exception as e:
        print_error(f"Ошибка соединения с MCP: {e}")
        return []

def analyze_tools(tools: List[Any]) -> Dict[str, Any]:
    """Анализирует полученные инструменты"""
    print_header("АНАЛИЗ ИНСТРУМЕНТОВ")
    
    analysis = {
        'total': len(tools),
        'jira_tools': [],
        'confluence_tools': [],
        'adf_tools': [],
        'other_tools': []
    }
    
    for tool in tools:
        name = tool.name
        if name.startswith('jira_'):
            analysis['jira_tools'].append(name)
        elif name.startswith('confluence_'):
            analysis['confluence_tools'].append(name)
            if 'adf' in name.lower():
                analysis['adf_tools'].append(name)
        else:
            analysis['other_tools'].append(name)
    
    # Статистика
    print_info(f"Всего инструментов: {analysis['total']}")
    print_info(f"Jira инструментов: {len(analysis['jira_tools'])}")
    print_info(f"Confluence инструментов: {len(analysis['confluence_tools'])}")
    print_info(f"ADF инструментов: {len(analysis['adf_tools'])}")
    
    return analysis

def test_adf_tools(tools: List[Any], analysis: Dict[str, Any]) -> bool:
    """Тестирует наличие и корректность ADF инструментов"""
    print_header("ТЕСТИРОВАНИЕ ADF ИНСТРУМЕНТОВ")
    
    expected_adf_tools = [
        'confluence_get_page_adf',
        'confluence_find_elements_adf', 
        'confluence_update_page_adf'
    ]
    
    success = True
    found_tools = analysis['adf_tools']
    
    print_info("Проверяем наличие ожидаемых ADF инструментов:")
    
    for expected_tool in expected_adf_tools:
        if expected_tool in found_tools:
            print_success(f"{expected_tool} - НАЙДЕН")
            
            # Находим полную информацию об инструменте
            tool_info = next((t for t in tools if t.name == expected_tool), None)
            if tool_info:
                print(f"    📝 Описание: {tool_info.description[:80]}...")
                if hasattr(tool_info, 'inputSchema') and tool_info.inputSchema:
                    params = tool_info.inputSchema.get('properties', {})
                    print(f"    🔧 Параметры: {', '.join(params.keys())}")
        else:
            print_error(f"{expected_tool} - НЕ НАЙДЕН")
            success = False
    
    # Проверяем дополнительные ADF инструменты
    extra_adf_tools = [tool for tool in found_tools if tool not in expected_adf_tools]
    if extra_adf_tools:
        print_info("Дополнительные ADF инструменты:")
        for tool in extra_adf_tools:
            print(f"    • {tool}")
    
    return success

def print_full_tool_list(tools: List[Any], analysis: Dict[str, Any]) -> None:
    """Печатает полный список всех инструментов по категориям"""
    print_header("ПОЛНЫЙ СПИСОК ИНСТРУМЕНТОВ")
    
    if analysis['adf_tools']:
        print(f"\n{Colors.BOLD}🆕 ADF ИНСТРУМЕНТЫ ({len(analysis['adf_tools'])}){Colors.END}")
        for i, tool_name in enumerate(analysis['adf_tools'], 1):
            print(f"  {i:2d}. {Colors.GREEN}{tool_name}{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 CONFLUENCE ИНСТРУМЕНТЫ ({len(analysis['confluence_tools'])}){Colors.END}")
    for i, tool_name in enumerate(analysis['confluence_tools'], 1):
        color = Colors.GREEN if 'adf' in tool_name.lower() else Colors.BLUE
        print(f"  {i:2d}. {color}{tool_name}{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎫 JIRA ИНСТРУМЕНТЫ ({len(analysis['jira_tools'])}){Colors.END}")
    for i, tool_name in enumerate(analysis['jira_tools'][:10], 1):  # Показываем первые 10
        print(f"  {i:2d}. {Colors.BLUE}{tool_name}{Colors.END}")
    
    if len(analysis['jira_tools']) > 10:
        print(f"     ... и еще {len(analysis['jira_tools']) - 10} Jira инструментов")

def print_summary(analysis: Dict[str, Any], adf_success: bool) -> None:
    """Печатает итоговую сводку"""
    print_header("ИТОГОВАЯ СВОДКА")
    
    print(f"📊 Статистика:")
    print(f"   • Всего инструментов: {analysis['total']}")
    print(f"   • Jira: {len(analysis['jira_tools'])}")
    print(f"   • Confluence: {len(analysis['confluence_tools'])}")
    print(f"   • ADF: {len(analysis['adf_tools'])}")
    
    if adf_success:
        print_success("ВСЕ ADF ИНСТРУМЕНТЫ НАЙДЕНЫ И ГОТОВЫ К РАБОТЕ!")
        print_info("Рекомендации:")
        print("   1. Перезапустите Claude Desktop полностью")
        print("   2. Пересоздайте MCP подключение если инструменты не видны")
        print("   3. Проверьте настройки claude_desktop_config.json")
    else:
        print_error("НЕКОТОРЫЕ ADF ИНСТРУМЕНТЫ НЕ НАЙДЕНЫ!")
        print_warning("Проверьте:")
        print("   1. Правильность регистрации инструментов в confluence.py")
        print("   2. Отсутствие синтаксических ошибок")
        print("   3. Корректность импортов ADF модулей")

async def main():
    """Главная функция тестирования"""
    print_header("ТЕСТ MCP ATLASSIAN ADF ИНСТРУМЕНТОВ")
    print_info("Запускаем полную диагностику...")
    
    # Тестируем соединение и получаем инструменты
    tools = await test_mcp_connection()
    
    if not tools:
        print_error("Не удалось получить список инструментов!")
        sys.exit(1)
    
    # Анализируем инструменты
    analysis = analyze_tools(tools)
    
    # Тестируем ADF инструменты
    adf_success = test_adf_tools(tools, analysis)
    
    # Показываем полный список
    print_full_tool_list(tools, analysis)
    
    # Итоговая сводка
    print_summary(analysis, adf_success)
    
    return 0 if adf_success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
