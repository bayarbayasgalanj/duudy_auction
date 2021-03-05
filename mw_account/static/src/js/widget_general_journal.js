odoo.define('mw_account.mw_account_general_journal_widget', function (require) {
    "use strict";

    var Widget= require('web.Widget');
    var MWReportWidget= require('mw_html_finance_report.mw_account_report_widget');

    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;
    var dialogs = require('web.view_dialogs');
    var AccountReportGeneralJournal = MWReportWidget.extend(FieldManagerMixin, {
        template : "mw_account.AccountReportGeneralJournal",
        init: function (parent, dataPoint) {
            this._super.apply(this, arguments);			
        },
        events: {
            "click .oe_timesheet_row td": "go_to",  
        },

        start: function () {
            var self = this;
//            this._render();
            return this._super.apply(this, arguments) 
        },
	 _render: function () {
            var self = this;
            var get_data = this.data;
            var data_ids = get_data.id;

            var self = this;
            var line_ids;

            var ds = new data.DataSet(this, 'mw.account.report');
//            this.display_data(this.odoo_context);
            ds.call('get_tran_balance_js', [data_ids]).then(function(result) {
                if ( result!=undefined){      
                    self.query_data = result;
                    self.line_ids = result['line_ids'];
		            self.display_data(self.odoo_context);
                }
            });
        },
           /////////
        display_data: function(data) {

            var self = this;
			var data_self = undefined;
			if (data.data){
				data_self = data.data.data;
			}
            console.log("=======DRAW=====22222gj:::", data_self);
			var account_moves = [];
			var dc={};
			if (data_self !=undefined){
				for (var i = 0; i < data_self.length; i++){
/*					console.log("=======DRAW=====33333:::", data_self[i]);
					console.log("=======DRAW=====44444:::", data_self[i][0]);
*/					dc={MoveID:i,
						Dd:data_self[i][0],
						Date:data_self[i][1],
						Number:data_self[i][2],
						Name:data_self[i][3],
						Debit:data_self[i][4],
						Credit:data_self[i][5],
						}
					account_moves.push(dc);
				}
			}

			console.log('account_movesaccount_movesaccount_move++++s ',account_moves)
		    function checkBoxChanged(time) {
		      var grid = $("#grid_report").data("kendoGrid");
		        $("#grid_report").css("font-size", "8px");
		    }			
			 $("#grid_report").kendoGrid({
            toolbar: ["excel" ,"pdf"],
            excel: {
                fileName: "General journal Export.xlsx",
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
							Date: { type: "date" },
							Number: { type: "string" },
							Name: { type: "number" },
							Debit: { type: "number" },
							Credit: { type: "number" },
//							Discontinued: { type: "boolean" }
						}
					}
				},
				pageSize: 4000
			},
			height: 650,
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
				{ field: "Dd", title:"Дд", width: "60px" },
				{field: "Date", title: "Огноо",  width: "150px",filterable: { multi: true },format: "{0: yyyy-MM-dd}" /*filterable: {
                                cell: {
                                    operator: "contains",
                                    suggestionOperator: "contains"
                                }
                            }*/
				},
				{field: "Number", title: "Дугаар",filterable: { multi: true }
				},				
				{field: "Name", title: "Гүйлгээний утга",filterable: { multi: true }
				},				
				{ field: "Debit", title: "Дебит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Debit, "n2")#',filterable: { multi: true }},
				{ field: "Credit", title: "Кредит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Credit, "n2")#',filterable: { multi: true } },
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
        'mw_account_general_journal_widget', AccountReportGeneralJournal
    );
	return AccountReportGeneralJournal;
});
