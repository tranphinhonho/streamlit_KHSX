# # pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib


from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pandas as pd
from datetime import datetime, timezone, timedelta
import io
from googleapiclient.http import MediaIoBaseDownload


folder_id = '1waAcjH-lsNiyPC-eYf-sYyQJ_NPxC8pL'  # Backup_Database

def check_existence_in_drive(name, is_folder=False, credentials_path='ggd-api-8aef69f9d57c.json'):
    # Phạm vi mà ứng dụng sẽ yêu cầu quyền truy cập
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # Xác thực và xây dựng dịch vụ Drive API
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # MIME type cho thư mục nếu kiểm tra sự tồn tại của thư mục
    mime_type = 'application/vnd.google-apps.folder' if is_folder else None

    # Tạo truy vấn tìm kiếm
    query = f"'{folder_id}' in parents and name = '{name}' and trashed = false"
    if mime_type:
        query += f" and mimeType = '{mime_type}'"

    # Thực hiện truy vấn tìm kiếm
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print(f"No {'folder' if is_folder else 'file'} found with name: {name}")
        return False, None

    # print(f"{'Folder' if is_folder else 'File'} '{name}' exists with ID: {items[0]['id']}")
    return True, items[0]['id']

def create_folder_in_drive(new_folder_name, credentials_path='ggd-api-8aef69f9d57c.json'):
    # Phạm vi mà ứng dụng sẽ yêu cầu quyền truy cập
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # Xác thực và xây dựng dịch vụ Drive API
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # Tạo metadata cho thư mục mới
    folder_metadata = {
        'name': new_folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [folder_id]
    }

    # Tạo thư mục mới
    folder = service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    print(f"Folder '{new_folder_name}' created with ID: {folder.get('id')}")
    return folder.get('id')

def delete_files_by_ids(file_ids, credentials_path='ggd-api-8aef69f9d57c.json'):
    # Xác thực với Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # Lặp qua danh sách các file ID và xóa từng file
    deleted_file_ids = []
    for file_id in file_ids:
        try:
            service.files().delete(fileId=file_id).execute()
            print(f"File with ID {file_id} has been deleted.")
            deleted_file_ids.append(file_id)
        except Exception as e:
            print(f"Failed to delete file with ID {file_id}. Error: {str(e)}")
    return deleted_file_ids

def delete_all_files_with_name_from_drive(file_name, credentials_path='ggd-api-8aef69f9d57c.json'):
    # Phạm vi mà ứng dụng sẽ yêu cầu quyền truy cập
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # Xác thực và xây dựng dịch vụ Drive API
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # Tìm tất cả các tệp dựa trên tên tệp và ID của thư mục
    query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print(f"No files found with name: {file_name}")
        return []

    deleted_file_ids = []

    # Lặp qua tất cả các tệp và xóa chúng
    for item in items:
        file_id = item['id']
        service.files().delete(fileId=file_id).execute()
        print(f"File '{file_name}' with ID: {file_id} has been deleted.")
        deleted_file_ids.append(file_id)

    return deleted_file_ids

def upload_to_drive(folder_id, file_path,file_name='', credentials_path='ggd-api-8aef69f9d57c.json'):
    try:
        # Lấy tên tệp từ đường dẫn tệp
        if file_name=='':
            file_name = os.path.basename(file_path)

        # Phạm vi mà ứng dụng sẽ yêu cầu quyền truy cập
        SCOPES = ['https://www.googleapis.com/auth/drive.file']

        # Xác thực và xây dựng dịch vụ Drive API
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)

        # Tạo metadata cho tệp
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        # Tạo một MediaFileUpload object
        media = MediaFileUpload(file_path, resumable=True)

        # Upload tệp
        file = service.files().create(body=file_metadata,media_body=media,fields='id').execute()
        return True,file.get('id')
    except Exception as e:
        return False, f"Lỗi: {str(e)}"


def list_files_in_folder_to_dataframe(folder_id, credentials_path='ggd-api-8aef69f9d57c.json'):
    # Xác thực với Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # Tạo truy vấn để lấy danh sách tất cả các file trong thư mục
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
    items = results.get('files', [])

    # Tạo DataFrame từ danh sách các file
    file_data = []
    if items:
        for item in items:
            file_id = item['id']
            file_name = item['name']
            last_modified = item['modifiedTime']

            # Chuyển đổi thời gian từ múi giờ UTC sang múi giờ Việt Nam (+7 giờ)
            last_modified_vn = datetime.fromisoformat(last_modified[:-1]).replace(tzinfo=timezone.utc) + timedelta(
                hours=7)
            last_modified_vn_str = last_modified_vn.strftime("%Y-%m-%d %H:%M:%S")

            file_data.append({'File ID': file_id, 'File Name': file_name, 'Last Modified (VN)': last_modified_vn_str})

    df = pd.DataFrame(file_data)
    return df

def download_file_from_drive(file_id, save_path, credentials_path='ggd-api-8aef69f9d57c.json'):
    # Xác thực với Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # Tải xuống tệp từ Google Drive
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(save_path, 'wb') as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")


# # Sử dụng hàm
# file_path = 'database.db'
# file_name='database.db'


# upload_to_drive(folder_id, file_path)

# file_name='database.db'
# delete_all_files_with_name_from_drive(folder_id, file_name)

# parent_folder_id = '1waAcjH-lsNiyPC-eYf-sYyQJ_NPxC8pL'  # ID của thư mục cha
# new_folder_name = 'HoSoDoanhNghiep_2'
# create_folder_in_drive(new_folder_name)

# # Sử dụng hàm để kiểm tra sự tồn tại của tệp
# parent_folder_id = '1waAcjH-lsNiyPC-eYf-sYyQJ_NPxC8pL'  # ID của thư mục cha
# file_name = 'database.db'
# exists, file_id = check_existence_in_drive(parent_folder_id, file_name)
# print(f"File exists: {exists}, File ID: {file_id}")
#
# # Sử dụng hàm để kiểm tra sự tồn tại của thư mục
# folder_name = 'NewFolder'
# exists, folder_id = check_existence_in_drive(parent_folder_id, folder_name, is_folder=True)
# print(f"Folder exists: {exists}, Folder ID: {folder_id}")