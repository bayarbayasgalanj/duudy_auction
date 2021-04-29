odoo.define('mw_motors.odometer_widget', function (require) {
	"use strict";

	var QWeb = require('web.core').qweb;
    var fields = require('web.basic_fields');
    var field_registry = require('web.field_registry');

	var OdometerWidget = fields.FieldChar.extend({
        _onInput: function () {
        	console.log('==_onInput==')
            return;
        },
        _getValue: function () {
        	console.log('==_getValue==')
            var $input = this.$el.find('input');
            var val = this.$el[0].value;
            return val;
        },
        _renderReadonly: function () {
        	console.log('==_renderReadonly==', this.value)
            this._super.apply(this, arguments);
            if (this.value) {
                this.$el.html(QWeb.render('odometer_widget', {
                    'widget':this,
                }));
                var container = this.el.firstElementChild
				var odometer = new Odometer(
				{ 
					auto: false,
					el: container, 
					duration: 900,
					value: 0, 
					theme: 'car',
					animation: 'count',
					format: '(,ddd).d',
				});
				container.innerHTML = this.value;
            }
        },
        _render: function () {
        	console.log('==_render==')
            return this._renderReadonly();
        },
	});

	field_registry.add('odometer_widget', OdometerWidget);
});

odoo.define('mw_motors.tire_position_widget', function (require) {
	"use strict";

	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var data = require('web.data');
	var FieldManagerMixin = require('web.FieldManagerMixin');
    
	var dialogs = require('web.view_dialogs');
	var core = require('web.core');
	var QWeb = core.qweb;

	var TirePositionWidget = Widget.extend(FieldManagerMixin, {
		template : "mw_motors.TirePositionWidget",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
			console.log("==INIT TirePositionWidget==");
        },
        start: function() {
	    	var self = this;
	    	console.log("==START TirePositionWidget==");
	    	if(self.data.position_format){
		    	if(self.data.tire_line){
			    	var ds = new data.DataSet(this, 'motors.car');
					ds.call('get_tire_line_datas', ['motors.car', self.data["id"]])
			            .then(function (res) {
			            	if(res){
			            		self.display_data(res,false);
		            		}
		            });
	            }
	            else{
	            	var ds = new data.DataSet(this, 'motors.car.setting');
					ds.call('get_position_format', ['motors.car.setting', self.data["id"]])
			            .then(function (res) {
			            	self.display_data(false,true);
		            });
	            }
            }
		},
		display_data: function(data, is_setting) {
			var self = this;
			self.$el.html(QWeb.render("mw_motors.TirePositionWidget", {widget: self}));
			var position_format = self.data.position_format
			console.log('==Technic tire line==');
			// Draw=================
			if(position_format){
				var tbody_tires = document.getElementById("tire_position");
	        	var tire_number = 1;
	        	var s = 0;
	        	var tire_icon = "/mw_motors/static/src/img/tire.png";
	        	var lines = position_format.split(",");
	        	for(var i=0;i<lines.length;i++){
	        		var tr = document.createElement("tr");
	        		tr.setAttribute("style", "height:130px");
	        		var pos = lines[i].split("-");
	            	var tire_count = parseInt(pos[1])/2;

	            	// Zvvn dugui
	            	var td1 = document.createElement("td");
	            	td1.setAttribute("align", "left");
	            	for(var j=1;j<=tire_count;j++){
	            		var str = "";
	            		var img=document.createElement("img");
	            		if(data){
	            			// Тухайн байрлал дээр дугуй байгаа эсэх
	            			if(tire_number in data){
	            				str = data[tire_number]['serial'] ? ": "+data[tire_number]['serial'] : '';
		            			img.setAttribute('data-tire_id', (data[tire_number]['tire_id'] ? data[tire_number]['tire_id'] : ''));
		        				img.setAttribute('class', "tire_to_open");
		        				s += 1;
	            			}
	            			else{
	            				img.setAttribute('class', "empty_tire");
	            			}
	        			}
	        			else{
	        				str = "";
	        			}
						img.setAttribute('src', tire_icon);
						img.setAttribute('title', tire_number.toString() + str);
						img.setAttribute('height', '100px');
						img.setAttribute('width', '40px');
						td1.appendChild(img);
	            		tire_number += 1;
	            	}
	                tr.appendChild(td1);

	                // Baruun dugui
	                var td2 = document.createElement("td");
	                td2.setAttribute('class', 'right_tires');
	            	for(var j=1;j<=tire_count;j++){
	            		var str = "";
	            		var img=document.createElement("img");
	            		if(data){
	            			// Тухайн байрлал дээр дугуй байгаа эсэх
	            			if(tire_number in data){
	            				str = data[tire_number]['serial'] ? ": "+data[tire_number]['serial'] : '';
		            			img.setAttribute('data-tire_id', (data[tire_number]['tire_id'] ? data[tire_number]['tire_id'] : ''));
		        				img.setAttribute('class', "tire_to_open");
		        				s += 1;
	            			}
	            			else{
	            				img.setAttribute('class', "empty_tire");
	            			}
	        			}
	        			else{
	        				str = "";
	        			}
						img.setAttribute('src', tire_icon);
						img.setAttribute('title', tire_number.toString() + str);
						img.setAttribute('height', '100px');
						img.setAttribute('width', '40px');
						td2.appendChild(img);
	            		tire_number += 1;
	            	}
	                tr.appendChild(td2);
	                // Мөр нэмэх
	                if(tbody_tires){
	                	tbody_tires.appendChild(tr);
	                }
	        	}
        	}
		},
	});
	widgetRegistry.add(
	    'tire_position_widget', TirePositionWidget
	);

	// Appointment Scheduling Boards widget
	var ASBoardWidget = Widget.extend(FieldManagerMixin, {
		template : "mw_motors.ASBoardWidget",
		events: {
            "click td.cell_clickable": "go_to",  
            "click div.cell_clickable": "go_to",  
            "click td.td_cell_empty": "go_to_create",
        },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'appointment.scheduling.board');
			ds.call('get_timetable_datas', ['appointment.scheduling.board', this.data["date_required"]])
	            .then(function (res) {
	            	self.times = res['times'];
	            	self.cells_limit = res['cells_limit'];
	            	self.timetable_lines = res['timetable_lines'];
	            	self.display_data(res);
            });
		},
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'appointment.scheduling.board');
			ds.call('get_timetable_datas', ['appointment.scheduling.board', dataPoint.data["date_required"]])
	            .then(function (res) {
	            	self.times = res['times'];
	            	self.cells_limit = res['cells_limit'];
	            	self.timetable_lines = res['timetable_lines'];
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=======DRAW=====", data);
			self.$el.html(QWeb.render("mw_motors.ASBoardWidget", {widget: self}));
		},
		go_to: function(event) {
          	var self = this;
          	var tt_id = JSON.parse($(event.currentTarget).data("id"));
          	var dialog = new dialogs.FormViewDialog(this, {
              	type: 'ir.actions.act_window',
              	res_model: 'car.repair.order',
              	res_id: tt_id,
              	views: [[false, 'form']],
              	target: 'new',
              	readonly: (this.query_data=='done'),
              	disable_multiple_selection: true,
          	}).open();
      	},
      	go_to_create: function(event) {
          	var self = this;
          	var stall_id = JSON.parse($(event.currentTarget).data("stall_id"));
          	var start_time = JSON.parse($(event.currentTarget).data("start_time"));
          	var dialog = new dialogs.FormViewDialog(this, {
              	type: 'ir.actions.act_window',
              	res_model: 'car.repair.order',
              	res_id: false,
              	views: [[false, 'form']],
              	target: 'new',
              	readonly: (this.query_data=='done'),
              	disable_multiple_selection: true,
              	context: {
                    stall_id: stall_id,
                    date: self.data.date_required,
                    time: start_time,
                },
          	}).open();
      	},
	});
	widgetRegistry.add(
	    'asb_board_widget', ASBoardWidget
	);

	// Job Planning Boards widget
	var JPBoardWidget = Widget.extend(FieldManagerMixin, {
		template : "mw_motors.JPBoardWidget",
		events: {
            "click td.cell_clickable": "go_to",  
            "click div.cell_clickable": "go_to",  
        },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'job.planning.board');
			ds.call('get_timetable_datas', ['job.planning.board', this.data["date_required"]])
	            .then(function (res) {
	            	self.times = res['times'];
	            	self.cells_limit = res['cells_limit'];
	            	self.timetable_lines = res['timetable_lines'];
	            	self.all_repair_orders = res['all_repair_orders'];
	            	self.display_data(res);
            });
		},
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'job.planning.board');
			ds.call('get_timetable_datas', ['job.planning.board', dataPoint.data["date_required"]])
	            .then(function (res) {
	            	self.times = res['times'];
	            	self.cells_limit = res['cells_limit'];
	            	self.timetable_lines = res['timetable_lines'];
	            	self.all_repair_orders = res['all_repair_orders'];
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=======DRAW=====", data);
			self.$el.html(QWeb.render("mw_motors.JPBoardWidget", {widget: self}));
		},
		go_to: function(event) {
          	var self = this;
          	var tt_id = JSON.parse($(event.currentTarget).data("id"));
          	var dialog = new dialogs.FormViewDialog(this, {
              	type: 'ir.actions.act_window',
              	res_model: 'car.repair.order',
              	res_id: tt_id,
              	views: [[false, 'form']],
              	target: 'new',
              	readonly: (this.query_data=='done'),
              	disable_multiple_selection: true,
          	}).open();
      	},
	});
	widgetRegistry.add(
	    'jpb_board_widget', JPBoardWidget
	);

	// Appointment Preparation Boards widget
	var APBoardWidget = Widget.extend(FieldManagerMixin, {
		template : "mw_motors.APBoardWidget",
		events: {
            "click td.cell_clickable": "go_to",  
            "click div.cell_clickable": "go_to",  
        },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'appointment.preparation.board');
			ds.call('get_timetable_datas', ['appointment.preparation.board', this.data["date_required"]])
	            .then(function (res) {
	            	self.all_repair_orders = res['all_repair_orders'];

	            	self.times = res['times'];
	            	self.days3_repair_orders = res['days3_repair_orders'];
	            	self.days2_repair_orders = res['days2_repair_orders'];
	            	self.days1_repair_orders = res['days1_repair_orders'];
	            	self.ordered_repair_orders = res['ordered_repair_orders'];
	            	self.delivered_repair_orders = res['delivered_repair_orders'];

					self.today_repair_orders = res['today_repair_orders'];
					self.today_psfu = res['today_psfu'];
	            	self.display_data(res);
            });
		},
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'appointment.preparation.board');
			ds.call('get_timetable_datas', ['appointment.preparation.board', dataPoint.data["date_required"]])
	            .then(function (res) {
	            	self.all_repair_orders = res['all_repair_orders'];

	            	self.times = res['times'];
	            	self.days3_repair_orders = res['days3_repair_orders'];
	            	self.days2_repair_orders = res['days2_repair_orders'];
	            	self.days1_repair_orders = res['days1_repair_orders'];
	            	self.ordered_repair_orders = res['ordered_repair_orders'];
	            	self.delivered_repair_orders = res['delivered_repair_orders'];

					self.today_repair_orders = res['today_repair_orders'];
					self.today_psfu = res['today_psfu'];
					self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=======DRAW=====", data);
			self.$el.html(QWeb.render("mw_motors.APBoardWidget", {widget: self}));
		},
		go_to: function(event) {
          	var self = this;
          	var tt_id = JSON.parse($(event.currentTarget).data("id"));
          	var dialog = new dialogs.FormViewDialog(this, {
              	type: 'ir.actions.act_window',
              	res_model: 'car.repair.order',
              	res_id: tt_id,
              	views: [[false, 'form']],
              	target: 'new',
              	readonly: (this.query_data=='done'),
              	disable_multiple_selection: true,
          	}).open();
      	},
	});
	widgetRegistry.add(
	    'apb_board_widget', APBoardWidget
	);

	// Job Progress Control Boards widget
	var JPCBoardWidget = Widget.extend(FieldManagerMixin, {
		template : "mw_motors.JPCBoardWidget",
		events: {
            "click div.cell_clickable": "go_to",  
        },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'job.progress.contral.board');
			ds.call('get_timetable_datas', ['job.progress.contral.board', this.data["date_required"]])
	            .then(function (res) {
	            	self.waiting_service_ros = res['waiting_service_ros'];
	            	self.being_serviced_ros = res['being_serviced_ros'];
	            	self.paused_ros = res['paused_ros'];
	            	self.waiting_inspection_ros = res['waiting_inspection_ros'];
	            	self.waiting_washing_ros = res['waiting_washing_ros'];
	            	self.waiting_invoicing_ros = res['waiting_invoicing_ros'];
	            	self.waiting_settlement_ros = res['waiting_settlement_ros'];
	            	
	            	self.display_data(res);
            });
		},
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'job.progress.contral.board');
			ds.call('get_timetable_datas', ['job.progress.contral.board', dataPoint.data["date_required"]])
	            .then(function (res) {
	            	self.waiting_service_ros = res['waiting_service_ros'];
	            	self.being_serviced_ros = res['being_serviced_ros'];
	            	self.paused_ros = res['paused_ros'];
	            	self.waiting_inspection_ros = res['waiting_inspection_ros'];
	            	self.waiting_washing_ros = res['waiting_washing_ros'];
	            	self.waiting_invoicing_ros = res['waiting_invoicing_ros'];
	            	self.waiting_settlement_ros = res['waiting_settlement_ros'];

	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=======DRAW=====", data);
			self.$el.html(QWeb.render("mw_motors.JPCBoardWidget", {widget: self}));
		},
		go_to: function(event) {
          	var self = this;
          	var tt_id = JSON.parse($(event.currentTarget).data("id"));
          	var dialog = new dialogs.FormViewDialog(this, {
              	type: 'ir.actions.act_window',
              	res_model: 'car.repair.order',
              	res_id: tt_id,
              	views: [[false, 'form']],
              	target: 'new',
              	readonly: (this.query_data=='done'),
              	disable_multiple_selection: true,
          	}).open();
      	},
	});
	widgetRegistry.add(
	    'jpcb_board_widget', JPCBoardWidget
	);
});