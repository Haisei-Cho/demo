"""
Tableau Server URL Extractor for TabJolt Testing
指定されたProjectから全てのView URLを取得し、TabJoltテスト用に出力する
"""

import tableauserverclient as TSC
import csv


def get_project_views(server_url: str, username: str, password: str,
                      project_name: str, site_id: str = "") -> list:
    """
    指定されたProject配下の全ViewのURLを取得する

    Args:
        server_url: Tableau Serverのアドレス
        username: ユーザー名
        password: パスワード
        project_name: 対象のProject名
        site_id: SiteのコンテンツURL（デフォルトサイトは空文字）

    Returns:
        list: View情報のリスト
    """
    # ユーザー名・パスワード認証を使用
    tableau_auth = TSC.TableauAuth(username, password, site_id=site_id)

    # PAT認証を使用する場合は以下に変更：
    # tableau_auth = TSC.PersonalAccessTokenAuth(token_name, token_secret, site_id=site_id)

    server = TSC.Server(server_url, use_server_version=True)
    server.add_http_options({'verify': False})  # SSL証明書を検証する場合はTrueに変更

    all_views = []

    with server.auth.sign_in(tableau_auth):
        # 対象Projectを検索
        projects, _ = server.projects.get()
        target_project = next((p for p in projects if p.name.lower() == project_name.lower()), None)

        if not target_project:
            print(f"Projectが見つかりません: {project_name}")
            print(f"利用可能なProject: {[p.name for p in projects]}")
            return []

        print(f"Project検出: {target_project.name} (ID: {target_project.id})")

        # 全Workbookを取得し、クライアント側でProjectでフィルタリング
        # 注意: ProjectIdはサーバー側フィルタリングに対応していないため
        all_workbooks = list(TSC.Pager(server.workbooks))
        workbooks = [wb for wb in all_workbooks if wb.project_id == target_project.id]
        print(f"{len(workbooks)}件のWorkbookを検出（全{len(all_workbooks)}件中）")

        # 各WorkbookのViewを取得
        for wb in workbooks:
            server.workbooks.populate_views(wb)
            for view in wb.views:
                view_info = {
                    "workbook_name": wb.name,
                    "view_name": view.name,
                    "content_url": view.content_url,
                    "tabjolt_url": f"/views/{view.content_url}"
                }
                all_views.append(view_info)
            print(f"  - {wb.name}: {len(wb.views)}件のView")

    return all_views


def export_urls(views: list, csv_file: str = "tabjolt_urls.csv", txt_file: str = "tabjolt_urls.txt"):
    """URLをファイルに出力する"""
    # CSV形式
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Workbook", "View"])
        for view in views:
            writer.writerow([view["tabjolt_url"], view["workbook_name"], view["view_name"]])

    # テキスト形式
    with open(txt_file, 'w', encoding='utf-8') as f:
        for view in views:
            f.write(view["tabjolt_url"] + "\n")

    print(f"\n{len(views)}件のURLを {csv_file} と {txt_file} に出力しました")


def main():
    # ========== 設定 ==========
    SERVER_URL = "https://your-tableau-server.com"
    USERNAME = "your_username"          # ユーザー名
    PASSWORD = "your_password"          # パスワード
    SITE_ID = ""                        # SiteのコンテンツURL（デフォルトサイトは空文字）
    PROJECT_NAME = "Your Project Name"  # 対象のProject名
    # ==========================

    views = get_project_views(SERVER_URL, USERNAME, PASSWORD, PROJECT_NAME, SITE_ID)

    if views:
        print(f"\n合計{len(views)}件のViewを検出:")
        for view in views:
            print(view["tabjolt_url"])

        export_urls(views)


if __name__ == "__main__":
    main()
