odoo.define('mw_html_finance_report.mw_account_report_widget', function (require) {
    "use strict";

    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;
    var dialogs = require('web.view_dialogs');
	console.log("=======DRAW=====123");
    var AccountReportTest = Widget.extend(FieldManagerMixin, {
        template : "mw_html_finance_report.AccountReportTest",
        init: function (parent, dataPoint) {
            this._super.apply(this, arguments);
            this.data = dataPoint.data;
			this.odoo_context = dataPoint.context;
/*		    $("head").append('<link rel="stylesheet" href="https://kendo.cdn.telerik.com/2020.2.617/styles/kendo.default-v2.min.css" />');*/
		    $("head").append('<link rel="stylesheet" href="/mw_html_finance_report/static/src/css/kendo.default-v2.min.css" />');
			$("head").append('<link rel="stylesheet" href="/mw_html_finance_report/static/src/css/base.css" />');
/*   		    $("head").append('<script src="https://kendo.cdn.telerik.com/2020.2.617/js/jquery.min.js"></script>');*/

/*   		    $("head").append('<script src="https://kendo.cdn.telerik.com/2020.2.617/js/jszip.min.js"></script>');
		
		    $("head").append('<script type="text/javascript" src="https://kendo.cdn.telerik.com/2020.2.617/js/kendo.all.min.js"></script>');*/

/*   		    $("head").append('<script src="https://kendo.cdn.telerik.com/2020.2.617/js/jszip.min.js"></script>');
		
		    $("head").append('<script type="text/javascript" src="https://kendo.cdn.telerik.com/2020.2.617/js/kendo.all.min.js"></script>');*/

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
//            this.display_data(this.data);
            ds.call('get_data_js', [data_ids]).then(function(result) {
                if ( result!=undefined){      
                    self.query_data = result;
                    self.line_ids = result['line_ids'];
/*		            console.log("=======DRAW=====line_ids11 ", self.line_ids);*/
		            self.display_data(self.line_ids);
//                    self.$el.html(QWeb.render("mw_timetable.HrTimetable", {widget: self}));
                }
            });
        },
           /////////
        display_data: function(data) {

            var self = this;
/*            console.log("=======DRAW=====22222", data);
            console.log("=======DRAW=====line_ids", self.line_ids);*/
			var account_moves = [];
			var dc={};
			for (var i = 0; i < self.line_ids.length; i++){
				dc={MoveID:i,
					Name:self.line_ids[i].name,
					Debit:self.line_ids[i].debit,
					Credit:self.line_ids[i].credit,
					Date:self.line_ids[i].date,
					}
				account_moves.push(dc);
				console.log('self.line_ids____ ',self.line_ids[i].date)
			}

			console.log('data:account_moves++++ ',account_moves);
			
			 $("#grid_report").kendoGrid({
            toolbar: ["excel" ,"pdf"],
            excel: {
                fileName: "Kendo UI Grid Export.xlsx",
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
				schema: {
					model: {
						fields: {
							Name: { type: "string" },
							Date: { type: "string" },
							Debit: { type: "number" },
							Credit: { type: "number" },
//							Discontinued: { type: "boolean" }
						}
					}
				},
				pageSize: 4000
			},
//			height: 550,
			scrollable: true,
			sortable: true,
			filterable: true,
			pageable: {
				input: true,
				numeric: false
			},
			 filterable: {
                            mode: "row"
                        },
			columns: [
				{field: "Name", title: "Description", filterable: {
                                cell: {
                                    operator: "contains",
                                    suggestionOperator: "contains"
                                }
                            }
				},
				{ field: "Date", title:"Date", width: "130px" },
				{ field: "Debit", title: "debit",  width: "130px" },
				{ field: "Credit", title: "Credit", width: "130px" },
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
        'mw_account_report_widget', AccountReportTest
    );
	return AccountReportTest;
});
