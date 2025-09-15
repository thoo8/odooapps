odoo.define('thoo8_appointment.portal_form', function (require) {

    'use strict';

    const publicWidget = require('web.public.widget');
    const ajax = require('web.ajax');

    const rpc = require('web.rpc');

    const core = require('web.core');
    const _t = core._t;

    publicWidget.registry.AppointmentRequestForm = publicWidget.Widget.extend({
        selector: '#appointment-container',
        events: {
            'click #send-otp': '_onSendOTP',
            'click #submit_appointment': '_onSubmitClick',
            'change select[name="service_type"]': '_onServiceTypeChange',
            'change select[name="gender"]': '_onGenderChange',
            'click #next-to-step-2': '_nextStep1',
            'click #back-to-step-1': '_backToStep1',
            'click #next-to-step-3': '_nextStep2',
            'click #back-to-step-2': '_backToStep2',
        },

        start: function () {
            this._super.apply(this, arguments);
            this.mobileVerificationEnabled = $('#mobile_verification_flag').val() === 'True';
            this.idCardVerificationEnabled = $('#id_card_verification_flag').val() === 'True';

            // نتأكد أن النموذج موجود قبل تنفيذ أي كود wizard
            const $form = this.$('#appointment-request-form');
            if ($form.length) {
                const serviceTypeSelect = $form.find('select[name="service_type"]');
                if (serviceTypeSelect.val()) {
                    this._onServiceTypeChange({ currentTarget: serviceTypeSelect });
                }
            }

            // ✅ نخفي شاشة بعد 5 ثواني من التحميل بعد ما يجهزDOM
            setTimeout(() => {
                this._hidePreloader();
            }, 5000);
        },

        // ✅ دالة تخفي شاشة التحميل
        _hidePreloader: function () {
            const preloader = document.getElementById('page-preloader');
            if (preloader) {
                preloader.style.opacity = '0';
                setTimeout(() => preloader.style.display = 'none', 500);
            }
        },

        // =================== التنقل بين الخطوات ===================
        _nextStep1: function (ev) {
            ev.preventDefault();
            if (this._validateStep1()) {
                $('#step-1').hide();
                $('#step-2').show();
            }
        },

        _backToStep1: function (ev) {
            ev.preventDefault();
            $('#step-1').show();
            $('#step-2').hide();
        },

        _nextStep2: function (ev) {
            ev.preventDefault();
            if (this._validateStep2()) {
                this._showSummary();
                $('#step-2').hide();
                $('#step-3').show();
            }
        },

        _backToStep2: function (ev) {
            ev.preventDefault();
            $('#step-2').show();
            $('#step-3').hide();
        },

        // =================== تحقق Step 1 ===================
        _validateStep1: function () {
            this._clearErrors();
            let hasError = false;
            const service_type = this.$('select[name="service_type"]').val();
            const gender = this.$('select[name="gender"]').val();
            const appointment_date = this.$('input[name="appointment_date"]').val();
            const appointment_time = this.$('input[name="appointment_time"]').val();
            const serviceData = this.lastServiceData || {};

            if (!service_type) {
                this._showError('.error-service-type', _t('يرجى اختيار الغرض من الموعد.'));
                hasError = true;
            }

            if (serviceData.gender === 'both' && !gender) {
                this._showError('.error-gender', _t('يرجى اختيار القسم من القائمة.'));
                hasError = true;
            }

            // تحقق الجدولة فقط إذا مطلوبة
            let scheduleRequired = false;
            if ((gender === 'male' && serviceData.enable_male_schedule) ||
                (gender === 'female' && serviceData.enable_female_schedule)) {
                scheduleRequired = true;
            }

            if (scheduleRequired) {
                if (!appointment_date) {
                    this._showError('.error-appointment_date', _t('يرجى اختيار تاريخ الموعد'));
                    hasError = true;
                }
                if (!appointment_time) {
                    this._showError('.error-appointment_time', _t('يرجى اختيار وقت الموعد'));
                    hasError = true;
                }
            }

            return !hasError;
        },

        // =================== تحقق Step 2 ===================
        _validateStep2: function () {
            this._clearErrors();
            let hasError = false;
            const beneficiaryName = this.$('input[name="beneficiary_name"]').val().trim();
            const id_card = this.$('input[name="id_card"]').val().trim();
            const mobile = this.$('input[name="mobile"]').val().trim();
            const code_entered = this.$('input[name="otp"]').val();
            const expected_code = window.localStorage.getItem('otp_code');

            if (!beneficiaryName || beneficiaryName.split(/\s+/).length < 3) {
                this._showError('.error-beneficiary-name', _t('يرجى كتابة الاسم الكامل باستخدام احرف عربية.'));
                hasError = true;
            }
            if (!id_card) {
                this._showError('.error-id-card', _t('رقم الهوية مطلوب'));
                    hasError = true;
            }
            console.log(this.idCardVerificationEnabled)
            if (this.idCardVerificationEnabled){
                if (!/^[12]\d{9}$/.test(id_card)) {
                    this._showError('.error-id-card', _t('رقم الهوية غير صحيح'));
                    hasError = true;
                }
            }
            if (!/^05\d{8}$/.test(mobile)) {
                this._showError('.error-mobile', _t('رقم الجوال غير صحيح'));
                hasError = true;
            }
            if (this.mobileVerificationEnabled) {
                if (!code_entered || code_entered != expected_code) {
                    this._showError('.error-otp-code', _t('رمز التحقق غير صحيح'));
                    hasError = true;
                }
            }

            return !hasError;
        },

        _showSummary: function () {
            const serviceText = this.$('select[name="service_type"] option:selected').text();
            const genderText = this.$('select[name="gender"] option:selected').text();
            const date = this.$('input[name="appointment_date"]').val();
            const time = this.$('input[name="appointment_time"]').val();
            const name = this.$('input[name="beneficiary_name"]').val();
            const idCard = this.$('input[name="id_card"]').val();
            const mobile = this.$('input[name="mobile"]').val();

            // الحصول على قيمة الوقت المعروضة بدل الـ ID
            let timeText = '-';
            const $activeTimeBtn = this.$('#available-times button.active');
            if ($activeTimeBtn.length) {
                timeText = $activeTimeBtn.text();
            }

            const serviceData = this.lastServiceData || {};
            const gender = this.$('select[name="gender"]').val();

            // تحديد إذا كانت الجدولة مطلوبة
            let scheduleRequired = false;
            if ((gender === 'male' && serviceData.enable_male_schedule) ||
                (gender === 'female' && serviceData.enable_female_schedule)) {
                scheduleRequired = true;
            }

            // بناء HTML للملخص
            let summaryHtml = `<div class="row g-2 p-3 m-5 border shadow-sm rounded bg-light">`;

            function addItem(title, value) {
                summaryHtml += `
                    <div class="col-12 col-md-3 p-2 border"><strong>${title}</strong></div>
                    <div class="col-12 col-md-9 p-2 border bg-white">${value}</div>
                `;
            }

            addItem(_t('الخدمة'), serviceText);
            addItem(_t('القسم'), genderText);

            if (scheduleRequired) {
                addItem(_t('التاريخ'), date || '-');
                addItem(_t('الوقت'), timeText || '-');
            }

            addItem(_t('المستفيد'), name);
            addItem(_t('رقم الهوية'), idCard);
            addItem(_t('رقم الجوال'), mobile);

            summaryHtml += `</div>`;

            $('#confirmation-summary').html(summaryHtml);
        },

        // دالة عرض خطأ
        _showError: function (selector, message) {
            this.$el.find(selector).text(message);
        },

        // دالة عرض نجاح
        _showSuccess: function (selector, message) {
            this.$el.find(selector).text(message);
        },

        _clearErrors: function () {
            this.$el.find('#form-errors').empty();
            this.$el.find('.text-danger').text('');
        },

        _clearSuccess: function () {
            this.$el.find('.success-otp-sent').empty();
            this.$el.find('.text-success').text('');
        },

        _hideScheduleFields: function () {
            $('#appointment_date, #appointment_time')
                .closest('.form-group')
                .hide();
        },

        _showScheduleFields: function () {
            $('#appointment_date, #appointment_time')
                .closest('.form-group')
                .show();
        },

        _onSendOTP: function (ev) {
            ev.preventDefault();
            this._clearErrors();
            this._clearSuccess();

            const $btn = this.$el.find('#send-otp');
            const mobile = this.$el.find('input[name="mobile"]').val();

            if (!/^05\d{8}$/.test(mobile)) {
                this._showError('.error-mobile', _t('يرجى كتابة رقم جوال صحيح.'));
                return;
            }

            $btn.prop('disabled', true);
            ajax.jsonRpc("/thoo8/appointment/send_otp", 'call', { mobile: mobile }).then((res) => {

                if (res.success) {
                    this._showSuccess('.success-otp-sent', _t('✅ تم إرسال رمز التحقق.'));
                    window.localStorage.setItem('otp_code', res.code);

                    let counter = 60;
                    const interval = setInterval(() => {
                        if (counter > 0) {
                            $btn.text(_t(`إعادة ارسال خلال (${counter--})`));
                        } else {
                            clearInterval(interval);
                            $btn.prop('disabled', false).text(_t('إرسال رمز التحقق'));
                        }
                    }, 1000);
                } else {
                    this._showError('#form-errors', _t('Error while sending: ') + res.message);
                    $btn.prop('disabled', false).text(_t('إرسال رمز التحقق'));
                    return;
                }
            }).catch((err) => {
                // معالجة أي أخطاء غير متوقعة
                console.error(err);
                this._showError('.error-otp-code', _t('حدث خطأ غير متوقع، حاول مرة أخرى.'));
                $btn.prop('disabled', false).text(_t('إرسال رمز التحقق'));
                return;  // 🚫 وقف التنفيذ إذا صار استثناء
            });
        },

        // دالة التحكم بالظهور والإخفاء حسب الخدمة والجنس
        _updateGenderAndScheduleVisibility: function () {
            const serviceData = this.lastServiceData || {};
            const $genderBox = this.$el.find('#gender-selection');
            const $dateField = this.$el.find('input[name="appointment_date"]').closest('.form-group');
            const $timeField = this.$el.find('input[name="appointment_time"]').closest('.form-group');
            const selectedGender = this.$el.find('select[name="gender"]').val();

            // إخفاء كل الحقول أولاً
            $genderBox.hide();
            $dateField.hide();
            $timeField.hide();

            if (!serviceData || !serviceData.gender) return;

            // إذا الخدمة لكل الجنسين
            if (serviceData.gender === 'both') {
                $genderBox.show();
                $dateField.prop('required', false);
                $timeField.prop('required', false);

                // لو أول مرة (المستخدم ما اختار لسه) نخليها فاضية
                if (!selectedGender) {
                    $genderBox.find('select').val('');
                }

                // إذا اختار المستخدم قسم
                if (selectedGender === 'male' && serviceData.enable_male_schedule) {
                    $dateField.show();
                    // بعد اختيار الخدمة مباشرة، جلب التواريخ المتاحة
                    this._fetchAvailableDates();
                    $dateField.prop('required', true);
                    $timeField.prop('required', true);
                } else if (selectedGender === 'female' && serviceData.enable_female_schedule) {
                    $dateField.show();
                    // بعد اختيار الخدمة مباشرة، جلب التواريخ المتاحة
                    this._fetchAvailableDates();
                    $dateField.prop('required', true);
                    $timeField.prop('required', true);
                }
            } else {
                // الخدمة لجنس واحد فقط
                let genderName = serviceData.gender; // 'male' أو 'female'
                $genderBox.find('select').val(genderName); // نعبي الاختيار
                // إذا الخدمة لهذا الجنس مطلوبة للجدولة
                if ((genderName === 'male' && serviceData.enable_male_schedule) ||
                    (genderName === 'female' && serviceData.enable_female_schedule)) {
                    $dateField.show();
                    // بعد اختيار الخدمة مباشرة، جلب التواريخ المتاحة
                    this._fetchAvailableDates();
                }
            }
        },

        // اختيار الخدمة
        _onServiceTypeChange: function (ev) {
            const serviceTypeId = $(ev.currentTarget).val();
            const $noteDiv = this.$el.find('#service-note-display');
            const $scheduleField = this.$el.find('input[name="schedule_id"]');
            const $selectedGender = this.$el.find('select[name="gender"]');
            this.$el.find('#next-to-step-2').show();

            // إعادة ضبط التاريخ والوقت
            this._resetDateTimeSelection();

            if (!serviceTypeId) {
                $noteDiv.hide().empty();
                this.lastServiceData = null;
                this._updateGenderAndScheduleVisibility();
                return;
            }

            ajax.jsonRpc('/get_service_note', 'call', { service_type_id: serviceTypeId }).then((res) => {
                this.lastServiceData = res;

                let noteMessage = res.note || '';
                $scheduleField.val('');
                $selectedGender.val('');

                if (res.gender === 'both') {
                    noteMessage = noteMessage || _t('Please select the department.');
                } else {
                    let genderName = res.gender === 'male' ? _t('Male') : _t('Female');
                    noteMessage = _t(`This appointment is for the department ${genderName}. `) + noteMessage;

                    // تعبئة schedule_id مباشرة إذا موجودة
                    if (res.gender === 'male') $scheduleField.val(res.schedule_male_id || '');
                    else $scheduleField.val(res.schedule_female_id || '');
                }
                function isHTML(str) {
                    // نحذف كل التاجات من النص
                    const withoutTags = str.replace(/<[^>]*>/g, '').trim();
                    // لو بعد الحذف ما بقي أي نص → يعني كله تاجات
                    return withoutTags.length === 0 && /<[^>]+>/.test(str);
                }

                if (isHTML(noteMessage)) {
                    $noteDiv.hide().empty();
                } else {
                    $noteDiv.html(noteMessage).show();
                }
                // تحديث ظهور الجنس والجدولة
                this._updateGenderAndScheduleVisibility();

            });
        },

        // اختيار الجنس
        _onGenderChange: function (ev) {
            const serviceData = this.lastServiceData || {};
            const selectedGender = this.$el.find('select[name="gender"]').val();
            const $scheduleField = this.$el.find('input[name="schedule_id"]');
            this.$el.find('#next-to-step-2').show();

            // إعادة ضبط التاريخ والوقت
            this._resetDateTimeSelection();

            if (selectedGender === 'male' && serviceData.enable_male_schedule) {
                $scheduleField.val(serviceData.schedule_male_id || '');
            } else if (selectedGender === 'female' && serviceData.enable_female_schedule) {
                $scheduleField.val(serviceData.schedule_female_id || '');
            } else {
                $scheduleField.val('');
            }

            // تحديث ظهور التاريخ والوقت بعد اختيار الجنس
            this._updateGenderAndScheduleVisibility();
        },

        _renderCalendar: function (availableDates) {
            const self = this;
            const $calendarBody = this.$el.find('#calendar-body');
            const $calendarTitle = this.$el.find('#calendar-title');
            const $prevBtn = this.$el.find('#prev-month');
            const $nextBtn = this.$el.find('#next-month');

            // تحويل التواريخ المتاحة إلى Set لسهولة الفحص
            const availableSet = new Set(availableDates.map(d => d.date));

            // تحديد أقرب تاريخ متاح كبداية
            let currentDate = new Date(availableDates[0].date);

            // تحديد نطاق المواعيد
            const minDate = new Date(availableDates[0].date);
            const maxDate = new Date(availableDates[availableDates.length - 1].date);

            function renderMonth(year, month) {
                $calendarBody.empty();

                // عنوان الشهر
                const monthName = new Date(year, month).toLocaleString('ar-EG', { month: 'long', year: 'numeric' });
                $calendarTitle.text(monthName);

                const firstDay = new Date(year, month, 1);
                const lastDay = new Date(year, month + 1, 0);
                let startDay = firstDay.getDay();
                let totalDays = lastDay.getDate();

                let row = $('<tr></tr>');
                for (let i = 0; i < startDay; i++) {
                    row.append('<td></td>');
                }

                let hasAvailableDay = false;

                for (let day = 1; day <= totalDays; day++) {
                    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                    const cell = $('<td></td>').text(day);

                    if (dateStr === new Date().toISOString().split('T')[0]) {
                        cell.addClass('today-day');
                    }

                    if (availableSet.has(dateStr)) {
                        hasAvailableDay = true;
                        cell.addClass('selectable-day').css('cursor', 'pointer');
                        cell.on('click', function () {
                            $calendarBody.find('td').removeClass('selected-day');
                            $(this).addClass('selected-day');
                            self.$el.find('input[name="appointment_date"]').val(dateStr);
                            self._fetchAvailableTimes(dateStr);
                            self.$el.find('#appointment_time-selection').show();
                        });
                    } else {
                        cell.addClass('text-muted');
                    }

                    row.append(cell);

                    if ((day + startDay) % 7 === 0) {
                        $calendarBody.append(row);
                        row = $('<tr></tr>');
                    }
                }

                if (row.children().length) {
                    $calendarBody.append(row);
                }

                // التحكم في زر السابق
                $prevBtn.prop('disabled', year <= minDate.getFullYear() && month <= minDate.getMonth());

                // التحكم في زر التالي
                if (year >= maxDate.getFullYear() && month >= maxDate.getMonth()) {
                    $nextBtn.prop('disabled', true);
                } else {
                    $nextBtn.prop('disabled', false);
                }

                // إذا الشهر ما فيه مواعيد
                if (!hasAvailableDay) {
                    $calendarBody.html(`
                        <tr>
                            <td colspan="7" class="text-center text-muted py-5">
                                <i class="fa fa-calendar-times fa-3x mb-3"></i>
                                <div>${_t('There are no appointments available this month.')}</div>
                            </td>
                        </tr>
                    `);
                }
            }

            // أول عرض
            renderMonth(currentDate.getFullYear(), currentDate.getMonth());

            // زر السابق
            $prevBtn.off('click').on('click', function () {
                do {
                    currentDate.setMonth(currentDate.getMonth() - 1);
                } while (currentDate >= minDate && !monthHasAvailableDate(currentDate));
                renderMonth(currentDate.getFullYear(), currentDate.getMonth());
            });

            // زر التالي
            $nextBtn.off('click').on('click', function () {
                let found = false;
                while (currentDate < maxDate) {
                    currentDate.setMonth(currentDate.getMonth() + 1);
                    if (monthHasAvailableDate(currentDate)) {
                        found = true;
                        break;
                    }
                }
                if (found) {
                    renderMonth(currentDate.getFullYear(), currentDate.getMonth());
                } else {
                    // لا توجد مواعيد إضافية
                    $calendarBody.html(`
                        <tr>
                            <td colspan="7" class="text-center text-muted py-5">
                                <i class="fa fa-calendar-times fa-3x mb-3"></i>
                                <div>${_t('There are no appointments available.')}</div>
                            </td>
                        </tr>
                    `);
                }
            });

            // فحص إذا الشهر يحتوي مواعيد
            function monthHasAvailableDate(date) {
                const year = date.getFullYear();
                const month = date.getMonth() + 1;
                return Array.from(availableSet).some(d => {
                    const dObj = new Date(d);
                    return dObj.getFullYear() === year && (dObj.getMonth() + 1) === month;
                });
            }

            this.$el.find('#appointment-calendar').show();
        },

        // استدعاء التواريخ المتاحة
        _fetchAvailableDates: function () {
            const self = this;
            const scheduleId = this.$el.find('input[name="schedule_id"]').val();
            if (!scheduleId) return;

            const $calendar = self.$el.find('#appointment-calendar');
            const $scheduler = self.$el.find('#appointment-scheduler');
            $scheduler.hide();
            $calendar.hide().after(`
                <div id="calendar-loading" class="text-center py-5">
                    <i class="fa fa-spinner fa-spin fa-3x text-primary"></i>
                </div>
            `);

            ajax.jsonRpc('/get_available_dates', 'call', { schedule_id: scheduleId }).then((res) => {
                $('#calendar-loading').remove();
                if (res.dates && res.dates.length) {
                    $scheduler.show();
                    self.$el.find('#next-to-step-2').show();
                    self._renderCalendar(res.dates);
                } else {
                    $scheduler.show();
                    $calendar.show();
                    self.$el.find('#next-to-step-2').hide();
                    self.$el.find('#calendar-body').html(`
                        <tr>
                            <td colspan="7" class="text-center text-muted py-4">
                                <i class="fa fa-calendar-times fa-2x mb-2"></i>
                                <div>${_t('There are no appointments available now.')}ً</div>
                            </td>
                        </tr>
                    `);
                }
            });
        },

        // استدعاء الأوقات المتاحة
        _fetchAvailableTimes: function(date) {
            const self = this;
            const scheduleId = this.$el.find('input[name="schedule_id"]').val();
            const $timesDiv = this.$el.find('#available-times');
            $timesDiv.empty();
            if (!date || !scheduleId) return;

            // 🔹 إظهار لودر أثناء تحميل الأوقات
            $timesDiv.html(`
                <div id="times-loading" class="text-center py-4 m-au">
                    <i class="fa fa-spinner fa-spin fa-3x text-primary"></i>
                </div>
            `);

            ajax.jsonRpc('/get_available_times', 'call', { schedule_id: scheduleId, date: date }).then((res) => {
                $timesDiv.empty(); // إزالة اللودر

                if (res.times && res.times.length) {

                    const now = new Date(); // الوقت الحالي
                    const todayStr = now.toISOString().split('T')[0]; // yyyy-mm-dd

                    // فلترة الأوقات: لو التاريخ اليوم -> نستبعد الأوقات الماضية
                    const filteredTimes = res.times.filter(function(time) {
                        if (date === todayStr) {
                            const slotDateTime = new Date(date + " " + time.time); // صياغة الوقت
                            return slotDateTime > now; // نحتفظ فقط بالمستقبل
                        }
                        return true; // لو التاريخ مو اليوم نخلي كل الأوقات
                    });

                    if (filteredTimes.length) {
                        filteredTimes.forEach(function(time) {
                            const btn = $('<button type="button" class="btn btn-sm"></button>')
                                .text(time.time)
                                .data('time-id', time.id)
                                .on('click', function() {
                                    $timesDiv.find('button').removeClass('active btn-primary').addClass('btn-outline-secondary');
                                    $(this).removeClass('btn-outline-secondary').addClass('btn-primary active');
                                    self.$el.find('input[name="appointment_time"]').val(time.id); // حفظ slot id
                                });
                            btn.addClass('btn-outline-secondary'); // الشكل الافتراضي
                            $timesDiv.append(btn);
                        });
                    } else {
                        $timesDiv.append(`
                            <div class="text-muted text-center py-3">
                                <i class="fa fa-clock fa-2x mb-2"></i>
                                <div>${_t('There are no time available now.')}</div>
                            </div>
                        `);
                    }

                } else {
                    $timesDiv.append(`
                        <div class="text-muted text-center py-3">
                            <i class="fa fa-clock fa-2x mb-2"></i>
                            <div>${_t('There are no time available.')}</div>
                        </div>
                    `);
                }
            });
        },

        _resetDateTimeSelection: function() {
            const $datesDiv = this.$el.find('#available-dates');
            const $timesDiv = this.$el.find('#available-times');

            // إزالة زرون التاريخ والوقت النشطة
            $datesDiv.find('button').removeClass('active');
            $timesDiv.find('button').removeClass('active');

            // تفريغ الحقول
            this.$el.find('input[name="appointment_date"]').val('');
            this.$el.find('input[name="appointment_time"]').val('');
        },

        _onSubmitClick: function (ev) {

            ev.preventDefault();
            this._clearErrors();
            let hasError = false;
            const self = this;

            const $form = $(ev.currentTarget).closest('form');
            const beneficiaryName = $form.find('input[name="beneficiary_name"]').val().trim();
            const service_type = $form.find('select[name="service_type"]').val();
            const id_card = $form.find('input[name="id_card"]').val().trim();
            const mobile = $form.find('input[name="mobile"]').val().trim();
            const code_entered = $form.find('input[name="otp"]').val();
            const expected_code = window.localStorage.getItem('otp_code');
            const gender = $form.find('select[name="gender"]').val();
            const schedule_id = $form.find('input[name="schedule_id"]').val();
            const appointment_date = $form.find('input[name="appointment_date"]').val();
            const appointment_time = $form.find('input[name="appointment_time"]').val();

            if (!beneficiaryName || beneficiaryName.split(/\s+/).length < 3) {
                this._showError('.error-beneficiary-name', _t('يرجى كتابة الاسم الكامل باستخدام احرف عربية.'));
                hasError = true;
            }
            if (!id_card) {
                this._showError('.error-id-card', _t('ID number Required.'));
                    hasError = true;
            }
            if(this.idCardVerificationEnabled){
                if (!/^[12]\d{9}$/.test(id_card)) {
                    this._showError('.error-id-card', _t('Invalid ID number.'));
                    hasError = true;
                }
            }
            if (!/^05\d{8}$/.test(mobile)) {
                this._showError('.error-mobile', _t('Invalid Mobile Number'));
                hasError = true;
            }
            if (!service_type) {
                this._showError('.error-service-type', _t('Please select the purpose of the appointment.'));
                hasError = true;
            }
            if (this.mobileVerificationEnabled) {
                if (!code_entered || code_entered != expected_code) {
                    this._showError('.error-otp-code', _t('Invalid OTP code'));
                    hasError = true;
                }
            }

            // ✅ التحقق الجديد للجنس والجدولة (مبني على lastServiceData)
            const serviceData = this.lastServiceData || {};

            // إذا الخدمة تتطلب اختيار الجنس (both) ولم يختر المستخدم
            if (serviceData.gender === 'both' && !gender) {
                this._showError('.error-gender', _t('Please select the department (Male or Female).'));
                hasError = true;
            }

            // تحقق إذا القسم المختار عليه جدولة
            let scheduleRequired = false;

            if (serviceData.gender === 'male' && gender === 'male' && serviceData.enable_male_schedule) {
                scheduleRequired = true;
            } else if (serviceData.gender === 'female' && gender === 'female' && serviceData.enable_female_schedule) {
                scheduleRequired = true;
            } else if (serviceData.gender === 'both') {
                if ((gender === 'male' && serviceData.enable_male_schedule) ||
                    (gender === 'female' && serviceData.enable_female_schedule)) {
                    scheduleRequired = true;
                }
            }

            // إذا مطلوب الجدولة للقسم المختار
            if (scheduleRequired) {
                if (!appointment_date) {
                    this._showError('.error-appointment_date', _t('يرجى اختيار تاريخ الموعد'));
                    hasError = true;
                }
                if (!appointment_time) {
                    this._showError('.error-appointment_time', _t('يرجى اختيار وقت الموعد'));
                    hasError = true;
                }
            }

            if (hasError) return;

            Promise.all([
                ajax.jsonRpc('/validate_otp_session', 'call', {
                    otp_code: code_entered,
                    mobile: mobile
                }),
                ajax.jsonRpc('/check_duplicate_id', 'call', {
                    id_card: id_card,
                    service_type: service_type
                }),
            ]).then(function (results) {
                const otpResult = results[0];
                const duplicateResult = results[1];

                $('#warning-idcard-duplicate').hide();

                if (self.mobileVerificationEnabled) {
                    if (!otpResult.valid) {
                        self._showError('.error-otp-code', _t('رمز التحقق غير صحيح او منتهي الصلاحية.'));
                        return;
                    }
                }

                if (duplicateResult.exists) {
                    $('#warning-idcard-duplicate').show();
                    let mobilePart = duplicateResult.mobile.substring(7, 11);
                    self._showError('.warning-idcard-duplicate',
                        _t('لديك طلب سابق باسم ') + duplicateResult.beneficiary_name +
                        _t('، سيتم ابلاغكم بالموعد على رقم الجوال المنتهي بـ ') + mobilePart);
                    return;
                }

                $form[0].submit();
            });
        }

    });

    return publicWidget.registry.AppointmentRequestForm;
});