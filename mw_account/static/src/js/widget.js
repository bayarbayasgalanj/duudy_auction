odoo.define('mw_account.mw_account_tran_report_widget', function (require) {
    "use strict";

    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;
    var dialogs = require('web.view_dialogs');
	console.log("=======DRAW=====123");
    var AccountReportTranBalance = Widget.extend(FieldManagerMixin, {
        template : "mw_account.AccountReportTranBalance",
        init: function (parent, dataPoint) {
            this._super.apply(this, arguments);
            this.data = dataPoint.data;
			this.odoo_context = dataPoint.context;
/*            console.log("-----=======DRAW=====dataPoint.context ", dataPoint.context);*/
		    $("head").append('<link rel="stylesheet" href="/mw_html_finance_report/static/src/css/kendo.default-v2.min.css" />');
			$("head").append('<script type="text/javascript" src="/mw_html_finance_report/static/lib/js/jszip.min.js"></script>');
			
			$("head").append('<script type="text/javascript" src="/mw_html_finance_report/static/lib/js/kendo.all.min.js"></script>');
			
			
        },
        events: {
            "click .oe_timesheet_row td": "go_to",  
        },

        start: function () {
            var self = this;
            this._render();
            return this._super.apply(this, arguments) 
        },
	 _render: function () {
            var self = this;
            var get_data = this.data;
            var data_ids = get_data.id;

            var self = this;
            var line_ids;

//            var ds = new data.DataSet(this, 'account.account');
            var ds = new data.DataSet(this, 'mw.account.report');
//            this.display_data(this.odoo_context);
            ds.call('get_tran_balance_js', [data_ids]).then(function(result) {
                if ( result!=undefined){      
                    self.query_data = result;
                    self.line_ids = result['line_ids'];
		            self.display_data(self.odoo_context);
//                    self.$el.html(QWeb.render("mw_timetable.HrTimetable", {widget: self}));
                }
            });
        },
           /////////
        display_data: function(data) {

            var self = this;
			var data_self = data.data;
//            console.log("=======DRAW=====22222:::", data_self);
			var account_moves = [];
			var dc={};
			if (data_self !=undefined){
				for (var i = 0; i < data_self.length; i++){
	/*				console.log("=======DRAW=====33333:::", data_self[i]);
					console.log("=======DRAW=====44444:::", data_self[i][0]);*/
					dc={MoveID:i,
						Dd:data_self[i][0],
						Code:data_self[i][1],
						Name:data_self[i][2],
						Idebit:data_self[i][3],
						Icredit:data_self[i][4],
						Debit:data_self[i][5],
						Credit:data_self[i][6],
						Edebit:data_self[i][7],
						Ecredit:data_self[i][8],
						}
					account_moves.push(dc);
				//	console.log('self.line_ids____ ',self.line_ids[i].date)
				}
			}

//			console.log('account_movesaccount_movesaccount_move++++s ',account_moves)
			 $("#grid_report").kendoGrid({
            toolbar: ["excel" ,"pdf"],
            excel: {
                fileName: "Tran balance Export.xlsx",
                filterable: true
            },
            pdf: {
                allPages: true,
                avoidLinks: true,
                paperSize: "A4",
                margin: { top: "2cm", left: "1cm", right: "1cm", bottom: "1cm" },
                landscape: true,
                repeatHeaders: true,
                template: $("#page-template").html(),
                scale: 0.8
            },
			dataSource: {
				data:account_moves,
				batch: true,
				schema: {
					model: {
						fields: {
							Dd: { type: "string" },
							Code: { type: "string" },
							Name: { type: "string" },
							Idebit: { type: "number" },
							Icredit: { type: "number" },
							Debit: { type: "number" },
							Credit: { type: "number" },
							Edebit: { type: "number" },
							Ecredit: { type: "number" },
//							Discontinued: { type: "boolean" }
						}
					}
				},
				pageSize: 4000
			},
			height: 550,
			scrollable: true,
			sortable: true,
/*			pageable: {
				input: true,
				numeric: false
			},*/
/*			 filterable: {
                            mode: "row"
                        },*/
			filterable: true,
//			columnMenu: true,
			columns: [
				{ field: "Dd", title:"Дд", width: "40px" },
				{field: "Code", title: "Код",  width: "100px",filterable: { multi: true } /*filterable: {
                                cell: {
                                    operator: "contains",
                                    suggestionOperator: "contains"
                                }
                            }*/
				},
				{field: "Name", title: "Дансны нэр",filterable: { multi: true }
				},				
				{
				title: "Эхний үлдэгдэл",
					columns: [
					{ field: "Idebit", title:"Дебит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Idebit, "n2")#', filterable: { multi: true, search: true}, width: "150px"},
					{ field: "Icredit", title: "Кредит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Icredit, "n2")#',filterable: { multi: true }, width: "150px"},]
				},
				{ field: "Debit", title: "Дебит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Debit, "n2")#',filterable: { multi: true }, width: "150px"},
				{ field: "Credit", title: "Кредит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Credit, "n2")#',filterable: { multi: true } , width: "150px"},
				{
				title: "Эцсийн үлдэгдэл",
				columns: [					
					{ field: "Edebit", title: "Дебит",attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Edebit, "n2")#',filterable: { multi: true }, width: "150px"},
					{ field: "Ecredit", title: "Кредит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Ecredit, "n2")#' ,filterable: { multi: true }, width: "150px"},
					]
				}
			]
		});
			
        },
        go_to: function(event) {
          var self = this;
          var tt_id = JSON.parse($(event.target).data("id"));

          new dialogs.FormViewDialog(this, {
              type: 'ir.actions.act_window',
              res_model: 'hr.timetable.line',
              res_id: tt_id,
              view_type: 'form',
              view_mode: 'form',
              views: [[false, 'form']],
              target: 'new',
              readonly: (this.query_data=='done'),
              on_saved: this.trigger_up.bind(this, 'reload'),
          }).open();
        },
    });
    widgetRegistry.add(
        'mw_account_tran_report_widget', AccountReportTranBalance
    );
	return AccountReportTranBalance;
});
