from django.shortcuts import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from records.views import render, redirect_to_name
from records.models import Keypair
from spoonpi.nfc_reader import NFCReader

is_polling = False

@login_required
def keypairs_page(request):
	keypairs = Keypair.objects.all()
	return render(request, 'keypairs.html',  {'keypairs': keypairs})

@login_required
def scan_rfid(request):
	global is_polling
	if not is_polling:
		is_polling = True
		uid = NFCReader().read_tag()
		is_polling = False
		return HttpResponse(uid)
	else:
		response = HttpResponse("Please try again at a later time. Sorry for the inconvenience.")
		response.status_code = 400
		return response

@login_required
def new_keypair(request):
	name = request.POST['name']
	pin = request.POST['pin']
	rfid_uid = request.POST['rfid_uid']

	is_error = False

	if not (len(pin) == 0 or (len(pin) == 4 and pin.isdigit())):
		messages.add_message(request, messages.ERROR, 'PIN must be blank, or consists of 4 digits.')
		is_error = True

	if not rfid_uid:
		messages.add_message(request, messages.ERROR, 'The RFID UID must not be empty.')
		is_error = True

	if is_error:
		return redirect_to_name('keypairs')

	Keypair.objects.create(name = name, pin = pin, rfid_uid = rfid_uid)
	messages.add_message(request, messages.SUCCESS, 'Pair addition successful.')
	return redirect_to_name('keypairs')

@login_required
def edit_keypair_name(request):
	name = request.POST['value']
	Keypair.objects.filter(id = request.POST['kid']).update(name=name)
	return HttpResponse("Successful.")

@login_required
def edit_keypair_pin(request):
	pin = request.POST['value']

	if not (len(pin) == 0 or (len(pin) == 4 and pin.isdigit())):
		messages.add_message(request, messages.ERROR, 'PIN must be blank, or consist of 4 digits.')
		response = HttpResponse("Invalid PIN")
		response.status_code = 400
		return response
	else:
		Keypair.objects.filter(id = request.POST['kid']).update(pin=pin)
		return HttpResponse("Successful.")

@login_required
def edit_keypair_uid(request):
	Keypair.objects.filter(id = request.POST['kid']).update(rfid_uid=request.POST['value'])
	return HttpResponse("Successful.")

@login_required
def delete_keypair(request):
	Keypair.objects.filter(id = request.POST['kid']).delete()
	return HttpResponse("Successful.")

@login_required
def keypair_toggle_active(request):
	keypair = Keypair.objects.get(id = request.POST['kid'])
	keypair.is_active = not keypair.is_active
	keypair.save()
	return HttpResponse("Successful.")

@login_required
def print_pdf(request):
	from reportlab.lib import colors
	from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
	from reportlab.lib.pagesizes import letter
	from reportlab.lib.styles import getSampleStyleSheet

	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = 'attachment; filename="forkpi_keypairs.pdf"'

	doc = SimpleDocTemplate(response, pagesize=letter)
	elements = []
	styles = getSampleStyleSheet()
	style = styles['Normal']
	keypairs = Keypair.objects.all()

	data = []
	data.append(['Name', 'RFID UID'])

	for keypair in keypairs:
		if keypair.is_active:
			style.textColor = colors.black
		else:
			style.textColor = colors.gray
		data.append([Paragraph(str(keypair.name), style), Paragraph(str(keypair.rfid_uid), style)])
	
	t = Table(data, colWidths=[300, 100])
	t.setStyle(TableStyle([('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),('BOX', (0,0), (-1,-1), 0.25, colors.black),]))
	elements.append(t)
	doc.build(elements)
	return response