from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
import datetime
from .models import CustomUser, Staffs, Courses, Subjects, Students, Attendance, AttendanceReport, LeaveReportStudent, FeedBackStudent, StudentResult, SessionYearModel, NotificationStudent, Syllabus


# views.py

def student_home(request):
	# Getting Logged in Student Data
	student = Students.objects.get(admin=request.user.id)
	recent_notifications = NotificationStudent.objects.filter(student_id=student).order_by('-created_at')[:3]
	# Getting Course Enrolled of LoggedIn Student
	course = student.course_id 
	user = CustomUser.objects.get(id=request.user.id)
	notifications = NotificationStudent.objects.filter(student_id=student)
	# Getting the Subjects of Course Enrolled
	subjects = Subjects.objects.filter(course_id=course)

	context = {
		"subjects": subjects,
		"user": user,
		"student": student,
		"notifications": notifications,
		"recent_notifications": recent_notifications,
	}
	return render(request, "student_template/student_home_template.html", context)



def student_profile(request):
	user = CustomUser.objects.get(id=request.user.id)
	student = Students.objects.get(admin=user)

	context={
		"user": user,
		"student": student
	}
	return render(request, 'student_template/student_profile.html', context)



def student_view_attendance(request):
    student_obj = Students.objects.get(admin=request.user.id)
    total_attendance = AttendanceReport.objects.filter(student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(student_id=student_obj, status=False).count()
    course_obj = Courses.objects.get(id=student_obj.course_id.id)
    total_subjects = Subjects.objects.filter(course_id=course_obj).count()

	#total attendance percentage calculation (dinominator zero error handling)

    if total_attendance == 0:
        attendance_percentage = 0.0
    else:
        attendance_percentage = (attendance_present / total_attendance) * 100
    

    subject_name = []
    data_present = []
    data_absent = []
    percent = []
    subject_data = Subjects.objects.filter(course_id=student_obj.course_id)
    subject_name_and_id = list(subject_data.values_list('id', 'subject_name'))

    for subject in subject_data:
        attendance = Attendance.objects.filter(subject_id=subject.id)
        attendance_present_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance,
            status=True,
            student_id=student_obj.id
        ).count()
        attendance_absent_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance,
            status=False,
            student_id=student_obj.id
        ).count()

        denominator = attendance_present_count + attendance_absent_count
        if denominator == 0:
            attendance_percentage_count = 0.0
        else:
            attendance_percentage_count = (attendance_present_count / denominator) * 100


        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)
        percent.append(attendance_percentage_count)
    # Zip the lists in the view
    subject_data_zipped = zip(subject_name, data_present, data_absent, percent)


    context = {
        "total_attendance": total_attendance,
        "attendance_present": attendance_present,
        "attendance_absent": attendance_absent,
		"attendance_percent": attendance_present,
        "total_subjects": total_subjects,
        "subject_data": subject_data_zipped, 
		"subject_name": subject_name,
		"subject_name_and_id": subject_name_and_id,
		"attendance_percentage": attendance_percentage
		  # Pass the zipped data to the template
    }

    return render(request, "student_template/student_view_attendance.html", context)



def student_view_attendance_post(request):
	if request.method != "POST":
		messages.error(request, "Invalid Method")
		return redirect('student_view_attendance')
	else:
		# Getting all the Input Data
		subject_id = request.POST.get('subject')
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')

		# Parsing the date data into Python object
		start_date_parse = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
		end_date_parse = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

		# Getting all the Subject Data based on Selected Subject
		subject_obj = Subjects.objects.get(id=subject_id)
		
		# Getting Logged In User Data
		user_obj = CustomUser.objects.get(id=request.user.id)
		
		# Getting Student Data Based on Logged in Data
		stud_obj = Students.objects.get(admin=user_obj)

		# Now Accessing Attendance Data based on the Range of Date
		# Selected and Subject Selected
		attendance = Attendance.objects.filter(attendance_date__range=(start_date_parse,
																	end_date_parse),
											subject_id=subject_obj)
		# Getting Attendance Report based on the attendance
		# details obtained above
		attendance_reports = AttendanceReport.objects.filter(attendance_id__in=attendance,
															student_id=stud_obj)

		
		context = {
			"subject_obj": subject_obj,
			"attendance_reports": attendance_reports,
			"start_date": start_date_parse,
			"end_date": end_date_parse
		}

		return render(request, 'student_template/student_attendance_data.html', context)
		

def student_apply_leave(request):
	student_obj = Students.objects.get(admin=request.user.id)
	leave_data = LeaveReportStudent.objects.filter(student_id=student_obj)

	context = {
		"leave_data": leave_data
	}
	return render(request, 'student_template/student_apply_leave.html', context)



def student_apply_leave_save(request):
	if request.method != "POST":
		messages.error(request, "Invalid Method")
		return redirect('student_apply_leave')
	else:
		leave_date = request.POST.get('leave_date')
		leave_message = request.POST.get('leave_message')

		student_obj = Students.objects.get(admin=request.user.id)
		try:
			leave_report = LeaveReportStudent(student_id=student_obj,
											leave_date=leave_date,
											leave_message=leave_message,
											leave_status=0)
			leave_report.save()
			messages.success(request, "Applied for Leave.")
			return redirect('student_apply_leave')
		except:
			messages.error(request, "Failed to Apply Leave")
			return redirect('student_apply_leave')



def student_feedback(request):
	student_obj = Students.objects.get(admin=request.user.id)
	feedback_data = FeedBackStudent.objects.filter(student_id=student_obj)

	context = {
		"feedback_data": feedback_data
	}
	return render(request, 'student_template/student_feedback.html', context)



def student_feedback_save(request):
	if request.method != "POST":
		messages.error(request, "Invalid Method.")
		return redirect('student_feedback')
	else:
		feedback = request.POST.get('feedback_message')
		student_obj = Students.objects.get(admin=request.user.id)

		try:
			add_feedback = FeedBackStudent(student_id=student_obj,
										feedback=feedback,
										feedback_reply="")
			add_feedback.save()
			messages.success(request, "Feedback Sent.")
			return redirect('student_feedback')
		except:
			messages.error(request, "Failed to Send Feedback.")
			return redirect('student_feedback')



def student_profile(request):
	user = CustomUser.objects.get(id=request.user.id)
	student = Students.objects.get(admin=user)

	context={
		"user": user,
		"student": student
	}
	return render(request, 'student_template/student_profile.html', context)



def student_profile_update(request):
	if request.method != "POST":
		messages.error(request, "Invalid Method!")
		return redirect('student_profile')
	else:
		first_name = request.POST.get('first_name')
		last_name = request.POST.get('last_name')
		password = request.POST.get('password')
		address = request.POST.get('address')

		try:
			customuser = CustomUser.objects.get(id=request.user.id)
			customuser.first_name = first_name
			customuser.last_name = last_name
			if password != None and password != "":
				customuser.set_password(password)
			customuser.save()

			student = Students.objects.get(admin=customuser.id)
			student.address = address
			student.save()
			
			messages.success(request, "Profile Updated Successfully")
			return redirect('student_profile')
		except:
			messages.error(request, "Failed to Update Profile")
			return redirect('student_profile')



def student_view_result(request):
    student = Students.objects.get(admin=request.user.id)
    student_results = StudentResult.objects.filter(student_id=student.id)

    # Calculate total marks for each result
    for result in student_results:
        result.total_marks = result.subject_assignment_marks + result.subject_exam_marks

    context = {
        "student_result": student_results,
    }

    return render(request, "student_template/student_view_result.html", context)



def student_profile_update_page(request):
    # Retrieve existing user and student data
    user = request.user
    student = Students.objects.get(admin=user)

    context = {
        'user': user,
        'student': student,
    }

    return render(request, 'student_template/student_profile_update.html', context)



def subject_syllabus(request, subject_id):
    subject = Subjects.objects.get(id=subject_id)
    syllabus = Syllabus.objects.filter(subject_id=subject)
    context = {
        'subject': subject,
        'syllabus': syllabus,
    }
    return render(request, 'student_template/subject_syllabus.html', context)