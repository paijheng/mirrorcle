#from __future__ import print_function
import os
import io
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def main(is_update_file_function=False, update_drive_service_name=None, update_file_path=None):
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))
    print('*' * 10)

    if is_update_file_function is True:
        print(update_file_path + update_drive_service_name)
        print("=====執行上傳檔案=====")

        # 搜尋要上傳的檔案名稱是否有在雲端上並且刪除
        search_file(service=service, update_drive_service_name=update_drive_service_name,
                    is_delete_search_file=True)
        # 檔案上傳到雲端上
        update_file(service=service, update_drive_service_name=update_drive_service_name,
                    local_file_path=os.getcwd() + '/' + update_drive_service_name)
        print("=====上傳檔案完成=====")
        
def delete_drive_service_file(service, file_id):
    service.files().delete(fileId=file_id).execute()
    
def update_file(service, update_drive_service_name, local_file_path):

    print("正在上傳檔案...")
    file_metadata = {'name': update_drive_service_name}
    media = MediaFileUpload(local_file_path, )
    file_metadata_size = media.size()
    start = time.time()
    file_id = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    end = time.time()
    print("上傳檔案成功！")
    print('雲端檔案名稱為: ' + str(file_metadata['name']))
    print('雲端檔案ID為: ' + str(file_id['id']))
    print('檔案大小為: ' + str(file_metadata_size) + ' byte')
    print("上傳時間為: " + str(end-start))

    return file_metadata['name'], file_id['id']
     
def search_file(service, update_drive_service_name, is_delete_search_file=False):

    # Call the Drive v3 API
    results = service.files().list(fields="nextPageToken, files(id, name)", spaces='drive',
                                   q="name = '" + update_drive_service_name + "' and trashed = false",
                                   ).execute()
    items = results.get('files', [])
    if not items:
        print('沒有發現你要找尋的 ' + update_drive_service_name + ' 檔案.')
    else:
        print('搜尋的檔案: ')
        for item in items:
            times = 1
            print(u'{0} ({1})'.format(item['name'], item['id']))
            if is_delete_search_file is True:
                print("刪除檔案為:" + u'{0} ({1})'.format(item['name'], item['id']))
                delete_drive_service_file(service, file_id=item['id'])
            if times == len(items):
                return item['id']
            else:
                times += 1
'''
if __name__ == '__main__':
    #main(is_update_file_function=bool(True), update_drive_service_name='heart_rate_record.csv', update_file_path=os.getcwd() + '/')
'''