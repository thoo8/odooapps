odoo.define('thoo8_appointment.calendar', function(require){
    'use strict';
    const publicWidget = require('web.public.widget');

    publicWidget.registry.AppointmentCalendar = publicWidget.Widget.extend({
        selector: '#appointment-request-form',
        start: function(){
            this.$calendar = this.$('#appointment_calendar');
            this.$calendarTable = this.$('#calendar-table tbody');
            this.$currentMonthLabel = this.$('#current-month');
            this.$prevMonthBtn = this.$('#prev-month');
            this.$nextMonthBtn = this.$('#next-month');
            this.$availableTimes = this.$('#available-times');
            this.selectedDate = null;

            // بيانات تواريخ متاحة مؤقتة، سيتم جلبها من السيرفر حسب schedule_id
            this.availableDates = {}; // { '2025-08': [1,2,5,10,15], '2025-09': [3,4,7] }

            this.currentDate = new Date();
            this.currentMonth = this.currentDate.getMonth();
            this.currentYear = this.currentDate.getFullYear();

            this._renderCalendar();

            const self = this;
            this.$prevMonthBtn.on('click', function(){ self._changeMonth(-1); });
            this.$nextMonthBtn.on('click', function(){ self._changeMonth(1); });

            this.$calendarTable.on('click', 'td.available', function(){
                const day = $(this).data('day');
                self._selectDate(day);
            });
        },

        _renderCalendar: function(){
            const month = this.currentMonth;
            const year = this.currentYear;
            const firstDay = new Date(year, month, 1).getDay();
            const lastDate = new Date(year, month + 1, 0).getDate();

            this.$currentMonthLabel.text(new Date(year, month).toLocaleString('default',{month:'long', year:'numeric'}));
            this.$calendarTable.empty();

            let dayCount = 1;
            for(let i=0;i<6;i++){
                let row = $('<tr></tr>');
                for(let j=0;j<7;j++){
                    let cell = $('<td></td>');
                    if(i===0 && j<firstDay || dayCount>lastDate){
                        cell.addClass('disabled').text('');
                    } else {
                        cell.text(dayCount);
                        const monthKey = `${year}-${(month+1).toString().padStart(2,'0')}`;
                        if(this.availableDates[monthKey] && this.availableDates[monthKey].includes(dayCount)){
                            cell.addClass('available').data('day', dayCount);
                        } else {
                            cell.addClass('disabled');
                        }
                        dayCount++;
                    }
                    row.append(cell);
                }
                this.$calendarTable.append(row);
            }
            this._updateMonthNavigation();
        },

        _updateMonthNavigation: function(){
            const prevMonthKey = this._getMonthKey(this.currentYear, this.currentMonth-1);
            const nextMonthKey = this._getMonthKey(this.currentYear, this.currentMonth+1);
            this.$prevMonthBtn.prop('disabled', !this.availableDates[prevMonthKey]);
            this.$nextMonthBtn.prop('disabled', !this.availableDates[nextMonthKey]);
        },

        _getMonthKey: function(year, month){
            if(month<0){ year-=1; month=11; }
            else if(month>11){ year+=1; month=0; }
            return `${year}-${(month+1).toString().padStart(2,'0')}`;
        },

        _changeMonth: function(diff){
            this.currentMonth+=diff;
            if(this.currentMonth<0){ this.currentMonth=11; this.currentYear--; }
            if(this.currentMonth>11){ this.currentMonth=0; this.currentYear++; }
            this._renderCalendar();
        },

        _selectDate: function(day){
            this.$calendarTable.find('td').removeClass('selected');
            this.$calendarTable.find(`td.available[data-day=${day}]`).addClass('selected');
            this.selectedDate = new Date(this.currentYear, this.currentMonth, day);

            this.$availableTimes.show().empty();
            const exampleSlots = ['09:00','10:00','11:00']; // يمكن جلبها من السيرفر
            for(const slot of exampleSlots){
                const btn = $('<button type="button" class="btn btn-outline-primary btn-sm"></button>').text(slot);
                btn.on('click', ()=> { $('input[name="appointment_time"]').val(slot); });
                this.$availableTimes.append(btn);
            }
            $('input[name="appointment_date"]').val(`${this.currentYear}-${(this.currentMonth+1).toString().padStart(2,'0')}-${day.toString().padStart(2,'0')}`);
        },
    });
});
