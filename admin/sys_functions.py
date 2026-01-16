import os
import sqlite3
import pandas as pd
import datetime
from datetime import datetime, timedelta
import pytz
import openpyxl
import shutil
import bcrypt
import zipfile
import re
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import time
from io import BytesIO

DELIMITER = ' | '

def get_project_folder():
    return os.path.basename(os.getcwd())

def dataframe_to_json_string(df, orient='records', indent=1):
    """
    Chuyển đổi một DataFrame thành chuỗi JSON.

    Args:
        df (pd.DataFrame): DataFrame cần chuyển đổi.
        orient (str): Định dạng JSON (default: 'records').
            - 'split': Dictionary với keys ['index', 'columns', 'data'].
            - 'records': Danh sách các dictionary (mỗi hàng là một dictionary).
            - 'index': Dictionary với index làm key và cột làm giá trị.
            - 'columns': Dictionary với cột làm key.
            - 'values': Danh sách danh sách (giá trị).
        indent (int): Số khoảng cách thụt lề trong JSON (default: 4).

    Returns:
        str: Chuỗi JSON.
    """
    try:
        json_string = df.to_json(orient=orient, indent=indent, force_ascii=False)
        return json_string
    except Exception as e:
        return f"Error converting DataFrame to JSON: {e}"




def sanitize_sheet_name(name):
    # Lấy tối đa 31 ký tự và loại bỏ ký tự không hợp lệ
    sanitized = re.sub(r'[:\\/\?\*\[\]]', '', name)[:31]
    return sanitized or "Sheet1"  # Nếu tên rỗng, đặt tên mặc định

def tachma_list(lst, delimiter=' | ', index=0):
    """
    Tách mã từ list các chuỗi theo delimiter.
    Trả về list đã tách.
    Giữ nguyên None.
    """
    if not isinstance(lst, list):
        raise ValueError("Input phải là list")

    def safe_split(item):
        if item is None:
            return None
        try:
            parts = str(item).split(delimiter)
            if len(parts) > index:
                return parts[index].strip()
            return item  # Giữ nguyên nếu không có đủ phần tử
        except Exception:
            return item  # Giữ nguyên nếu có lỗi

    return [safe_split(item) for item in lst]


def tachma_text(text, delimiter=' | ', index=0):
    """
    Tách chuỗi theo delimiter, trả về phần tử tại vị trí index.
    Giữ nguyên None.
    """
    if text is None:
        return None
    try:
        parts = str(text).split(delimiter)
        if len(parts) > index:
            return parts[index].strip()
        return text  # Giữ nguyên nếu không có đủ phần tử
    except Exception:
        return text  # Giữ nguyên nếu có lỗi

def tachma_df(df: pd.DataFrame, column_names, delimiter=' | ', index=0):
    def safe_split(text, delimiter, index):
        # Giữ nguyên None
        if text is None:
            return None
        try:
            parts = str(text).split(delimiter)
            if len(parts) > index:
                return parts[index].strip()
            return text  # Trả về giá trị gốc nếu không có đủ phần tử
        except Exception:
            return text  # Trả về giá trị gốc nếu có lỗi

    for col in column_names:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: safe_split(x, delimiter, index))
    return df
    
def get_timestamp(strf = None):
    timestamp = datetime.now().timestamp()
    if strf:
        return str(timestamp)
    return timestamp

def list_files_and_folders_recursive(root_directory='.'):
    all_items = []

    for root, dirs, files in os.walk(root_directory):
        for name in dirs:
            all_items.append(os.path.join(root, name))
        for name in files:
            all_items.append(os.path.join(root, name))

    return all_items
# Function to check if the image exists
def check_image_path(img_path):
    # Path to the default image
    default_image_path = "images/NoImage.jpg"
    if img_path and os.path.exists(img_path):
        return img_path
    else:
        return default_image_path


def delete_image(image_path):
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# Hàm lấy đường dẫn ảnh trong thư mục
def get_image_paths(directory):
    # Các định dạng ảnh thường gặp
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}

    # Danh sách lưu đường dẫn các ảnh
    image_paths = []

    # Duyệt qua tất cả các file trong thư mục
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Kiểm tra xem file có định dạng ảnh không
            if any(file.lower().endswith(ext) for ext in image_extensions):
                # Thêm đường dẫn ảnh vào danh sách
                image_paths.append(os.path.join(root, file))

    return image_paths

# Hàm lưu tệp đã tải lên
def save_uploaded_file(uploaded_file, ma_san_pham, output_dir="AnhSanPham"):
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Lấy phần mở rộng của tệp gốc
    file_extension = os.path.splitext(uploaded_file.name)[1]
    # Đường dẫn file đích - sử dụng Path object
    file_path = Path(output_dir) / f"{ma_san_pham}{file_extension}"
    
    # Lưu ảnh
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path)

def get_current_directory(type='path'):
    """
    Lấy đường dẫn của thư mục chứa file Python hiện tại.

    type:
        - 'path' (mặc định): Trả về đường dẫn đầy đủ của thư mục.
        - 'folder': Trả về tên của thư mục.

    Returns:
        Đường dẫn hoặc tên thư mục chứa file hiện tại.
    """
    full_path = os.path.abspath(__file__)
    dir_path = os.path.dirname(full_path)

    if type == 'folder':
        return os.path.basename(dir_path)
    else:
        return dir_path
# print(get_current_directory(type='folder'))

# Tạo tệp ZIP
def create_zip(folders, zip_name='output.zip'):
    # Tạo tệp ZIP
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for folder in folders:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, os.path.join(folder, '..')))

def docso(conso, doiso1=" linh", doiso2=0):
    conso=str(conso)
    doiso1 = " " + doiso1.strip()
    s09 = ["", " một", " hai", " ba", " bốn", " năm", " sáu", " bảy", " tám", " chín"]
    lop3 = ["", " triệu", " nghìn", " tỷ"]

    if not conso.strip():
        return ""

    try:
        conso = float(conso)
        is_numeric = True
    except ValueError:
        is_numeric = False

    if is_numeric:
        if conso < 0:
            Dau = "âm "
        else:
            Dau = ""

        conso = round(abs(conso))
        conso = " " + str(conso).replace(",", "")

        if 'E' in conso:
            parts = conso.split('E')
            conso = parts[0].strip()
            sonhan = int(parts[1])
            conso = conso + "0" * (sonhan - len(conso) + 1)

        conso = conso.strip()
        sochuso = len(conso) % 9

        if sochuso > 0:
            conso = "0" * (9 - (sochuso % 12)) + conso

        DOCSO = ""
        i = 0
        lop = 1

        while i < len(conso):
            n1 = int(conso[i])
            n2 = int(conso[i + 1])
            n3 = int(conso[i + 2])
            baso = conso[i:i + 3]
            i += 3

            if n1 == 0 and n2 == 0 and n3 == 0:
                if DOCSO and lop == 3 and len(conso) - i > 2:
                    s123 = " tỷ"
                else:
                    s123 = ""
            else:
                if n1 == 0:
                    if not DOCSO:
                        s1 = ""
                    else:
                        s1 = " không trăm"
                else:
                    s1 = s09[n1] + " trăm"

                if n2 == 0:
                    if s1 == "" or n3 == 0:
                        s2 = ""
                    else:
                        s2 = doiso1
                else:
                    if n2 == 1:
                        s2 = " mười"
                    else:
                        s2 = s09[n2] + " mươi"

                if n3 == 1:
                    if n2 == 1 or n2 == 0:
                        s3 = " một"
                    else:
                        s3 = " mốt"
                elif n3 == 5 and n2 != 0:
                    s3 = " lăm"
                else:
                    s3 = s09[n3]

                if i >= len(conso):
                    s123 = s1 + s2 + s3
                else:
                    s123 = s1 + s2 + s3 + lop3[lop]

            lop += 1
            if lop > 3:
                lop = 1

            DOCSO += s123

            if i >= len(conso):
                break

        if DOCSO == "":
            DOCSO = "không"
        else:
            DOCSO = Dau + DOCSO.strip()
    else:
        DOCSO = conso
    if doiso2 == 0:
        DOCSO = DOCSO[0].upper() + DOCSO[1:]
    return DOCSO


def get_directory_list(base_folder):
    try:
        # Get list of all entries in the base_folder
        entries = os.listdir(base_folder)
        # Filter out only directories
        directories = [entry for entry in entries if os.path.isdir(os.path.join(base_folder, entry))]
        return directories
    except FileNotFoundError:
        return []

def delete_files(base_folder, sub_folder, files_to_delete):
    deleted_files = []
    not_found_files = []
    try:
        for file in files_to_delete:
            file_path = os.path.join(base_folder, sub_folder, file)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                deleted_files.append(file)
            else:
                not_found_files.append(file)
        return f"Đã xóa các file thành công!"
    except Exception as e:
        return f"Lỗi: {str(e)}"
def get_files_in_directory(folder_path):
    try:
        # Get list of all entries in the folder_path
        entries = os.listdir(folder_path)
        # Filter out only files
        files = [entry for entry in entries if os.path.isfile(os.path.join(folder_path, entry))]
        return files
    except FileNotFoundError:
        return []

def delete_directories(base_folder, directories_to_delete):
    try:
        for directory in directories_to_delete:
            directory_path = os.path.join(base_folder, directory)
            if os.path.exists(directory_path) and os.path.isdir(directory_path):
                shutil.rmtree(directory_path)
            else:
                return (f"Thư mục {directory} không tồn tại hoặc không phải là một thư mục hợp lệ.")
        return 'Đã xóa thư mục thành công!'
    except Exception as e:
        return f"Lỗi: {str(e)}"


def get_all_files_in_forms(base_folder):
    file_list = []
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            file_path = os.path.join(root, file)
            folder_path = root.replace(base_folder, '').lstrip(os.sep)
            file_list.append({'Tên thư mục': folder_path, 'Tên file': file})

    # Create DataFrame from the file list
    df_files = pd.DataFrame(file_list)
    df_files.index = df_files.index + 1
    df_files.reset_index(inplace=True)
    df_files.rename(columns={'index': 'STT'}, inplace=True)

    return df_files

def delete_file_in_folder(folder_path):
    # Duyệt qua tất cả các tệp tin trong thư mục
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # Kiểm tra xem đối tượng có phải là tệp tin không
        if os.path.isfile(file_path):
            # Xóa tệp tin
            os.remove(file_path)

def download_file(location,title,file_path,output_name, remove=True):
    with open(file_path, 'rb') as file:
        file_data = file.read()
        location.download_button(label=title, data=file_data, file_name=output_name)

def download_dataframe(df1,sheet_name1,show_index1=False, df2=None,sheet_name2=None,show_index2=False):
    
    
    output = BytesIO()

    # Xóa file gốc rồi tạo mới file
    with pd.ExcelWriter(output) as writer:
        df1.to_excel(writer, index=show_index1, sheet_name=sheet_name1)
    if df2:
        # ghép nối tiếp sheet vào dữ liệu hiện có
        with pd.ExcelWriter(output,  engine='openpyxl', mode='a') as writer:
            df2.to_excel(writer, index=show_index2, sheet_name=sheet_name2)
    processed_data = output.getvalue()
    return processed_data
def image_to_base64(img):
    if img:
        with BytesIO() as buffer:
            img.save(buffer, "png")
            return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    return None

def check_system_timezone_offset():
    # Lấy độ lệch múi giờ của hệ thống
    offset = datetime.now().astimezone().utcoffset()
    # Chuyển đổi độ lệch thành giờ
    offset_hours = offset.total_seconds() / 3600
    return offset_hours
def get_vietnam_time(second=True):
    # Lấy độ lệch múi giờ của hệ thống
    system_timezone_offset = check_system_timezone_offset()
    # Chuyển đổi múi giờ của hệ thống sang múi giờ Việt Nam (UTC+7)
    vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    # Tạo thời điểm hiện tại theo múi giờ hệ thống
    current_time = datetime.now(pytz.utc).astimezone()
    # Thêm hoặc bớt số giờ tương ứng với độ lệch giữa múi giờ hiện tại và múi giờ của Việt Nam
    vietnam_time = current_time + timedelta(hours=7 - system_timezone_offset)
    # Loại bỏ thông tin về múi giờ
    vietnam_time = vietnam_time.replace(tzinfo=None)
    if second:
        vietnam_time = vietnam_time.replace(microsecond=0)
    return vietnam_time


def hashpw(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# # Sử dụng hàm hashpw để mã hóa mật khẩu và lưu trữ trong cơ sở dữ liệu hoặc trạng thái phiên làm việc
# hashed_password = hashpw("Kde123")
#
# # Sau đó, khi cần kiểm tra mật khẩu, bạn sử dụng hàm check_password
# is_correct_password = check_password("Kde123", hashed_password)
# if is_correct_password:
#     print("Mật khẩu chính xác!")
# else:
#     print("Mật khẩu không chính xác!")


def get_part_text(data, indexes, delimiter=' | ', column_names=None):
    """
    Trích xuất các phần tử từ chuỗi dựa trên delimiter và danh sách chỉ mục.
    Hàm này có thể xử lý đầu vào là DataFrame, list, hoặc một chuỗi đơn lẻ.

    Args:
        data (pd.DataFrame, list, str): Dữ liệu đầu vào.
        indexes (list): Danh sách các chỉ mục (int) của các phần tử cần trích xuất.
        delimiter (str): Ký tự phân tách. Mặc định là ' | '.
        column_names (list, optional): Danh sách tên cột cần xử lý.
                                       Bắt buộc khi data là DataFrame.

    Returns:
        (pd.DataFrame, list, str): Dữ liệu đã được xử lý.
    """
    # Hàm nội bộ để xử lý một chuỗi đơn lẻ
    def _process_string(text):
        try:
            parts = str(text).split(delimiter)
            # Lấy các phần tử theo chỉ mục, bỏ qua các chỉ mục không hợp lệ
            selected_parts = [parts[i].strip() for i in indexes if i < len(parts)]
            return delimiter.join(selected_parts)
        except (AttributeError, IndexError):
            return text # Trả về giá trị gốc nếu có lỗi

    # Xử lý dựa trên loại dữ liệu đầu vào
    if isinstance(data, pd.DataFrame):
        if column_names is None:
            raise ValueError("Đối số 'column_names' là bắt buộc khi dữ liệu đầu vào là DataFrame.")
        
        df = data.copy() # Tránh sửa đổi DataFrame gốc
        for col in column_names:
            if col in df.columns:
                df[col] = df[col].apply(_process_string)
        return df

    elif isinstance(data, list):
        return [_process_string(item) for item in data]

    elif isinstance(data, str):
        return _process_string(data)

    else:
        # Trả về dữ liệu gốc nếu không phải là loại được hỗ trợ
        return data

def get_module_paths():
    """
    Quét các thư mục 'admin' và 'PagesKDE' trong thư mục làm việc hiện tại
    để lấy danh sách các module path.
    """
    module_paths = []
    target_folders = ['admin', 'PagesKDE']
    
    for folder in target_folders:
        # Giả định các thư mục này nằm cùng cấp với file main.py
        if os.path.isdir(folder):
            for filename in os.listdir(folder):
                if filename.endswith('.py') and filename != '__init__.py':
                    module_name = os.path.splitext(filename)[0]
                    module_path = f"{folder}.{module_name}"
                    module_paths.append(module_path)
                    
    return sorted(module_paths)
