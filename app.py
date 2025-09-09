# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os 
import uuid
from datetime import datetime

# Import models
from models.user import User, Student, Administrator
from models.course import Course
from models.registration import Registration
from models.json_handler import JSONHandler

# Import utils
from utils.authenticator import Authenticator
from utils.logger import Logger


def format_schedule_for_display(schedule):
    result = []
    for slot in schedule:
        result.append(f"{slot['day']} {slot['start_time']}-{slot['end_time']}")
    return ", ".join(result)


app = Flask(__name__)


@app.template_filter("format_schedule")
def format_schedule(schedule):
    result = []
    for slot in schedule:
        result.append(f"{slot['day']} {slot['start_time']}-{slot['end_time']}")
    return ", ".join(result)


def get_current_user(request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None

    users = JSONHandler.read_json("data/users.json") 
    for user_data in users:
        if user_data["user_id"] == user_id:
            return User.from_dict(user_data)

    return None


app.secret_key = "ReYHane1403"


# Initialize data files #مقدار دهی اولیه
def initialize_data_files():
    files = {
        "data/users.json": [],
        "data/courses.json": [],
        "data/registrations.json": [],
    }

    for file_path, default_data in files.items():
        if not os.path.exists(file_path):
            JSONHandler.write_json(file_path, default_data)

    users = JSONHandler.read_json("data/users.json")
    if not users:
        admin = Administrator(
            user_id=str(uuid.uuid4()),
            username="admin",
            password="RHane1403",
            name="مدیر سیستم",
        )
        users.append(admin.to_dict())
        JSONHandler.write_json("data/users.json", users)


initialize_data_files()


# Routes
@app.route("/") #صفحه اصلی سایت
def index():
    return render_template("index.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Authenticator.login(username, password)
        if user:
            session["user_id"] = user.user_id
            session["username"] = user.username
            session["role"] = user.role
            session["name"] = user.name

            flash("خوش آمدید!", "success")
            Logger.log_action("Login", f"User {username} logged in")

            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("courses"))
        else:
            flash("نام کاربری یا رمز عبور اشتباه است.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        name = request.form.get("name")

        if password != confirm_password:
            flash("رمزهای عبور مطابقت ندارند.", "danger")
            return render_template("register.html")

        if Authenticator.register(username, password, name):
            flash("ثبت نام با موفقیت انجام شد. اکنون می‌توانید وارد شوید.", "success")
            Logger.log_action("Registration", f"New user {username} registered")
            return redirect(url_for("login"))
        else:
            flash("این نام کاربری قبلاً استفاده شده است.", "danger")

    return render_template("register.html")


@app.route("/logout")
def logout():
    if "username" in session:
        Logger.log_action("Logout", f"User {session['username']} logged out")

    session.clear()
    flash("با موفقیت خارج شدید.", "info")
    return redirect(url_for("index"))


@app.route("/courses")
def courses():
    if "user_id" not in session:
        flash("لطفا ابتدا وارد شوید.", "warning")
        return redirect(url_for("login"))

    all_courses = JSONHandler.read_json("data/courses.json")

    registrations = JSONHandler.read_json("data/registrations.json")
    user_registrations = [
        r for r in registrations if r["user_id"] == session["user_id"]
    ]
    registered_course_ids = [r["course_id"] for r in user_registrations]

    return render_template(
        "courses.html", courses=all_courses, registered_courses=registered_course_ids
    )


@app.route("/course/<course_id>")
def course_detail(course_id):
    if "user_id" not in session:
        flash("لطفا ابتدا وارد شوید.", "warning")
        return redirect(url_for("login"))

    courses = JSONHandler.read_json("data/courses.json")
    course = next((c for c in courses if c["course_id"] == course_id), None)

    if not course:
        flash("دوره مورد نظر یافت نشد.", "danger")
        return redirect(url_for("courses"))

    registrations = JSONHandler.read_json("data/registrations.json")
    is_registered = any(
        r["user_id"] == session["user_id"] and r["course_id"] == course_id
        for r in registrations
    )

    current_registrations = sum(1 for r in registrations if r["course_id"] == course_id)

    return render_template(
        "course_detail.html",
        course=course,
        is_registered=is_registered,
        current_registrations=current_registrations,
    )


@app.route("/register_course/<course_id>") #ثبت نام دوره
def register_course(course_id): 
    if "user_id" not in session:
        flash("لطفا ابتدا وارد شوید.", "warning")
        return redirect(url_for("login"))

    courses = JSONHandler.read_json("data/courses.json")
    registrations = JSONHandler.read_json("data/registrations.json")

    course = next((c for c in courses if c["course_id"] == course_id), None)
    if not course:
        flash("دوره مورد نظر یافت نشد.", "danger")
        return redirect(url_for("courses"))

    if any(
        r["user_id"] == session["user_id"] and r["course_id"] == course_id
        for r in registrations
    ):
        flash("شما قبلاً در این دوره ثبت نام کرده‌اید.", "warning")
        return redirect(url_for("course_detail", course_id=course_id))
    
    course_registrations = sum(1 for r in registrations if r["course_id"] == course_id)
    if course_registrations >= course["capacity"]:
        flash("متاسفانه ظرفیت این دوره تکمیل شده است.", "danger")
        return redirect(url_for("course_detail", course_id=course_id))

    user_registrations = [
        r["course_id"] for r in registrations if r["user_id"] == session["user_id"]
    ]
    user_courses = [
        next((c for c in courses if c["course_id"] == reg_id), None)
        for reg_id in user_registrations
    ]
#regid شماره های درس های ثبت نام شده در تابع بالاست
    for registered_course in user_courses:
        if registered_course and has_schedule_conflict(
            registered_course["schedule"], course["schedule"]
        ):
            flash("تداخل زمانی با دوره دیگری که ثبت نام کرده‌اید وجود دارد.", "danger")
            return redirect(url_for("course_detail", course_id=course_id))

    if not check_prerequisites_met(session["user_id"], course["prerequisites"]):
        flash("شما پیش‌نیازهای لازم برای این دوره را ندارید.", "danger")
        return redirect(url_for("course_detail", course_id=course_id))
     #ما پیش نیاز نذاشتیم
    new_registration = Registration(
        reg_id=str(uuid.uuid4()),
        user_id=session["user_id"],
        course_id=course_id,
        registration_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    registrations.append(new_registration.to_dict())
    JSONHandler.write_json("data/registrations.json", registrations)
    #لاگر ثبت وقایع میکنه
    Logger.log_action(
        "Course Registration",#موضوع است
        f"User {session['username']} registered for course {course['title']}",
    )
    flash("با موفقیت در دوره ثبت نام شدید.", "success")
    return redirect(url_for("schedule"))


@app.route("/unregister_course/<course_id>") #لغو ثبت نام
def unregister_course(course_id):
    if "user_id" not in session:
        flash("لطفا ابتدا وارد شوید.", "warning")
        return redirect(url_for("login"))

    registrations = JSONHandler.read_json("data/registrations.json")
    courses = JSONHandler.read_json("data/courses.json")

    updated_registrations = [
        r
        for r in registrations
        if not (r["user_id"] == session["user_id"] and r["course_id"] == course_id)
    ]
    
    if len(updated_registrations) == len(registrations):
        flash("شما در این دوره ثبت نام نکرده‌اید.", "warning")
    else:
        course = next((c for c in courses if c["course_id"] == course_id), None)
        course_title = course["title"] if course else "Unknown Course"
        
        JSONHandler.write_json("data/registrations.json", updated_registrations)
        Logger.log_action(
            "Course Unregistration",
            f"User {session['username']} unregistered from course {course_title}",
        )
        flash("ثبت نام شما از این دوره لغو شد.", "success")

    return redirect(url_for("courses"))


@app.route("/schedule")
def schedule():
    if "user_id" not in session:
        flash("لطفا ابتدا وارد شوید.", "warning")
        return redirect(url_for("login"))

    registrations = JSONHandler.read_json("data/registrations.json")
    courses = JSONHandler.read_json("data/courses.json")

    user_registrations = [
        r for r in registrations if r["user_id"] == session["user_id"]
    ]
    user_courses = []

    for registration in user_registrations:
        course = next(
            (c for c in courses if c["course_id"] == registration["course_id"]), None
        )
        if course:
            user_courses.append(
                {**course, "registration_date": registration["registration_date"]}
            )

    return render_template("schedule.html", courses=user_courses)


@app.route("/profile", methods=["GET", "POST"]) #
def profile():
    if "user_id" not in session:
        flash("لطفا ابتدا وارد شوید.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        users = JSONHandler.read_json("data/users.json")
#i=شماره یوزر  #enumerate=شماره میده به اعضای یک لیست یا هر توالی . از 0 شروع میکند
        for i, user in enumerate(users):
            if user["user_id"] == session["user_id"]:
                new_name = request.form.get("name")
                if new_name:
                    users[i]["name"] = new_name
                    session["name"] = new_name

                new_password = request.form.get("new_password")
                confirm_password = request.form.get("confirm_password")
                current_password = request.form.get("current_password")

                if new_password:
                    if new_password != confirm_password:
                        flash("رمزهای عبور جدید مطابقت ندارند.", "danger")
                        return redirect(url_for("profile"))

                    if current_password != user["password"]:
                        flash("رمز عبور فعلی اشتباه است.", "danger")
                        return redirect(url_for("profile"))

                    users[i]["password"] = new_password

                JSONHandler.write_json("data/users.json", users)
                Logger.log_action(
                    "Profile Update",
                    f"User {session['username']} updated their profile",
                )
                flash("پروفایل شما با موفقیت به‌روزرسانی شد.", "success")
                break

    return render_template("profile.html")


# Admin routes
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session["role"] != "admin":
        flash("شما دسترسی لازم برای این صفحه را ندارید.", "danger")
        return redirect(url_for("index"))

    users = JSONHandler.read_json("data/users.json")
    courses = JSONHandler.read_json("data/courses.json")
    registrations = JSONHandler.read_json("data/registrations.json")

    # Count students
    students_count = sum(1 for u in users if u["role"] == "student")

    # Get course statistics
    course_stats = []
    for course in courses:
        reg_count = sum(
            1 for r in registrations if r["course_id"] == course["course_id"]
        )
        capacity = course["capacity"]

        course_stats.append(
            {
                "title": course["title"],
                "course_id": course["course_id"],
                "registered": reg_count,
                "capacity": capacity,
                "percentage": int((reg_count / capacity) * 100) if capacity > 0 else 0,
            }
        )

    return render_template(
        "admin/dashboard.html",
        students_count=students_count,
        courses_count=len(courses),
        registrations_count=len(registrations),
        course_stats=course_stats,
    )


@app.route("/admin/courses", methods=["GET", "POST"])
def admin_courses():
    current_user = get_current_user(request) #یک تابع برای گرفتن اطلاعات کاربر به صورت ریکوئست
    # if not current_user or current_user.role != "admin":
    #     flash("شما دسترسی لازم برای این صفحه را ندارید.", "danger")
    #     return redirect(url_for("index"))

    courses = JSONHandler.read_json("data/courses.json")

    # Add formatted schedule to each course
    for course in courses:
        formatted_schedule = []
        for slot in course["schedule"]:
            formatted_schedule.append(
                f"{slot['day']} {slot['start_time']}-{slot['end_time']}"
            )
        course["formatted_schedule"] = ", ".join(formatted_schedule)
    if request.method == "POST":
        action = request.form.get("action")
#اینجا میاد از ریکوئست فورممون با تابع گت اکشن مورد نظر کاربر را میگرد مثلا اد زدن دوره یا ادیت دوره
        if action == "add":
            # Add new course
            new_course = Course(
                course_id=str(uuid.uuid4()),
                title=request.form.get("title"),
                description=request.form.get("description"),
                schedule=parse_schedule(request.form.get("schedule")),#پارس تجزیه میکنه وساختار استاندار
                capacity=int(request.form.get("capacity")),
                prerequisites=(#پیش نیاز دوره
                    request.form.get("prerequisites", "").split(",")#اگه پیشنیاز نباشه ""خالی میده
                    if request.form.get("prerequisites")#اسپیلیت یک رشته ایجاد میکنه و،میذاره بین عضوها
                    else []
                ),
            )

            courses.append(new_course.to_dict())
            JSONHandler.write_json("data/courses.json", courses)
            Logger.log_action(
                "Course Added",
                f"Admin {session['username']} added course: {new_course.title}",
            )
            flash("دوره جدید با موفقیت اضافه شد.", "success")

        elif action == "edit":
            course_id = request.form.get("course_id")
            for i, course in enumerate(courses):
                if course["course_id"] == course_id:
                    courses[i]["title"] = request.form.get("title")
                    courses[i]["description"] = request.form.get("description")
                    courses[i]["schedule"] = parse_schedule(
                        request.form.get("schedule")
                    )
                    courses[i]["capacity"] = int(request.form.get("capacity"))
                    courses[i]["prerequisites"] = (
                        request.form.get("prerequisites", "").split(",")
                        if request.form.get("prerequisites")
                        else []
                    )

                    JSONHandler.write_json("data/courses.json", courses)
                    Logger.log_action(
                        "Course Updated",
                        f"Admin {session['username']} updated course: {courses[i]['title']}",
                    )
                    flash("دوره با موفقیت به‌روزرسانی شد.", "success")
                    break

        return redirect(url_for("admin_courses"))

    return render_template(
        "admin/manage_courses.html", courses=courses, current_user=current_user
    )


@app.route("/admin/delete_course/<course_id>")
def delete_course(course_id):
    if "user_id" not in session or session["role"] != "admin":
        flash("شما دسترسی لازم برای این عملیات را ندارید.", "danger")
        return redirect(url_for("index"))

    # Get courses and registrations
    courses = JSONHandler.read_json("data/courses.json")
    registrations = JSONHandler.read_json("data/registrations.json")

    course = next((c for c in courses if c["course_id"] == course_id), None)
    if course:
        course_title = course["title"]

        # Remove course
        updated_courses = [c for c in courses if c["course_id"] != course_id]

        updated_registrations = [
            r for r in registrations if r["course_id"] != course_id
        ]

        JSONHandler.write_json("data/courses.json", updated_courses)
        JSONHandler.write_json("data/registrations.json", updated_registrations)

        Logger.log_action(
            "Course Deleted",
            f"Admin {session['username']} deleted course: {course_title}",
        )
        flash("دوره با موفقیت حذف شد.", "success")
    else:
        flash("دوره مورد نظر یافت نشد.", "warning")

    return redirect(url_for("admin_courses"))


@app.route("/admin/users")#برای مدیریت کاربران
def admin_users():
    if "user_id" not in session or session["role"] != "admin":
        flash("شما دسترسی لازم برای این صفحه را ندارید.", "danger")
        return redirect(url_for("index"))

    users = JSONHandler.read_json("data/users.json")
    return render_template("admin/users.html", users=users)


# ===================== helper
def has_schedule_conflict(schedule1, schedule2):#بررسی تداخل زمانبندی
    for slot1 in schedule1:#اسلات شامل ساعت شروع و پایان و روز
        for slot2 in schedule2:
            if slot1["day"] == slot2["day"]:
                # Check for time overlap
                start1 = convert_time_to_minutes(slot1["start_time"])
                end1 = convert_time_to_minutes(slot1["end_time"])
                start2 = convert_time_to_minutes(slot2["start_time"])
                end2 = convert_time_to_minutes(slot2["end_time"])

                if max(start1, start2) < min(end1, end2):
                    return True #تداخل داره

    return False


def convert_time_to_minutes(time_str):
    # Convert "HH:MM"
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes
#مپ اینت دو بخش ساعت و دقیقه به اینت تبدیل میکنه

def check_prerequisites_met(user_id, prerequisites):
    return True
#همیشه پیش نیاز هارو پاس کرده

def parse_schedule(schedule_str):
    # Parse schedule
    if not schedule_str:
        return []

    schedule = []
    slots = schedule_str.split(",")
#بازه زمانی هست اسلات
    for slot in slots:
        slot = slot.strip()#فاصله اضافی اول اخر حذف میکند
        if not slot: #اگه فاصله ای نبود این اسلات رو رد میکنه میره بعدی
            continue

        parts = slot.split(" ")#در این متد وقتی برسه به چیزی که داخل پرانتز هست ویرگول میزنه
        if len(parts) >= 2:
            day = parts[0]
            time_range = parts[1]

            if "-" in time_range:
                start_time, end_time = time_range.split("-")
                schedule.append(
                    {"day": day, "start_time": start_time, "end_time": end_time}
                )

    return schedule


# run app
if __name__ == "__main__":
    app.run(debug=True)
#اگه فایل مستقیما اجرا شد هر فایل پایتونی که جای نیم بیاد،خط 570 اجرا میشه
