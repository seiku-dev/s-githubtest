"""Uploads an aab to the internal track."""

import argparse
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import httplib2
from oauth2client import client
from oauth2client.service_account import ServiceAccountCredentials


TRACK = 'internal'  # or can be 'alpha', beta', 'production' or 'rollout'

# workflow.yamlからの入力受付用
argparser = argparse.ArgumentParser(add_help=False)
# argparser.add_argument('package_name',
#                        default='com.example.githubtestproject',
#                        help='The package name. Example: com.android.sample')
argparser.add_argument('aab_file',
                       nargs='?',
                       default='app-release.aab',
                       help='The path to the AAB file')
argparser.add_argument('service_account_json',
                       nargs='?',
                       help='The path to the key file of service account.')


def main(argv):
  print('XXXXXXXXXX')

  scopes = ['https://www.googleapis.com/auth/androidpublisher']
  flags = argparser.parse_args()
  service_account_json = flags.service_account_json

  # サンプルではここがp12ファイルを利用していたため、サービスアカウントのjsonキーファイルで認証するように変更
  credentials = ServiceAccountCredentials.from_json_keyfile_name('app/pc-api-6432661342110974448-165-705320bcabc8.json', scopes=scopes)
  http = httplib2.Http()
  http = credentials.authorize(http)

  service = build('androidpublisher', 'v3', http=http)
  package_name = 'com.example.githubtestproject'
  aab_file = flags.aab_file

  try:
    edit_request = service.edits().insert(body={}, packageName='com.example.githubtestproject')
    result = edit_request.execute()
    edit_id = result['id']

    print('Edit ID : "%s"' % edit_id)

    # aabのアップロード(apkとはアップロード方法が異なるため注意)
    media = MediaFileUpload(aab_file, mimetype='application/octet-stream', resumable=True)
    aab_response = service.edits().bundles().upload(
        editId=edit_id,
        packageName='com.example.githubtestproject',
        media_body=media).execute()

    print('Version code %d has been uploaded' % aab_response['versionCode'])

    # Trackの更新(internal track)
    track_response = service.edits().tracks().update(
        editId=edit_id,
        track=TRACK,
        packageName='com.example.githubtestproject',
        body={u'releases': [{
            u'name': u'アップロード時の文言を指定',
            u'versionCodes': [str(aab_response['versionCode'])],
            u'status': u'completed',
        }]}).execute()

    print('Track %s is set with releases: %s' % (
        track_response['track'], str(track_response['releases'])))

    # Transactionのcommit
    commit_request = service.edits().commit(
        editId=edit_id, packageName='com.example.githubtestproject').execute()

    print('Edit "%s" has been committed' % (commit_request['id']))

  except client.AccessTokenRefreshError:
    print ('The credentials have been revoked or expired, please re-run the '
           'application to re-authorize')

if __name__ == '__main__':
  main(sys.argv)