odoo.define('mw_account.mw_account_partner_detail_widget', function (require) {
    "use strict";

    var Widget= require('web.Widget');
    var MWReportWidget= require('mw_html_finance_report.mw_account_report_widget');

    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;
    var dialogs = require('web.view_dialogs');
    var AccountReportPartnerDetail = MWReportWidget.extend(FieldManagerMixin, {
        template : "mw_account.AccountReportPartnerDetail",
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
			var data_self = data.data;
/*			if (data.data){
				data_self = data.data.data;
			}*/
//            console.log("=======DRAW=====22222pl:::", data_self);
			var account_moves = [];
			var dc={};
			if (data_self !=undefined){
				for (var i = 0; i < data_self.length; i++){
//					console.log("=======DRAW=====33333:::", data_self[i]);
					dc={MoveID:i,
						Dd:data_self[i].Dd,
						Date:data_self[i].Date,
						Number:data_self[i].Number,
						Account:data_self[i].Account,
						Name:data_self[i].Name,
						Debit:data_self[i].Debit,
						Credit:data_self[i].Credit,
						C2:data_self[i].C2,
						CAccount:data_self[i].CAccount,
						Branch:data_self[i].Branch,
					//	Istotal:is_color
						}
					account_moves.push(dc);
					
				}
			}


//		console.log('account_movesaccount_movesaccount_move++++s ',account_moves)
			 $("#grid_report").kendoGrid({
            toolbar: ["excel" ,"pdf","search"],
            excel: {
                fileName: "Partner Ledger Export.xlsx",
              //  filterable: true
            },
			//custom excel
			excelExport: function(e) {
                  var sheet = e.workbook.sheets[0];
                  var rows = sheet.rows;
                  var rowIdx, colIdx, cells, cell;
				  sheet.freezePane = { colSplit: 0, rowSplit: 5 };
    
			       for (var i = 0; i < e.workbook.sheets[0].rows.length; i++) {
			            var $row = e.workbook.sheets[0].rows[i];
						if ($row.type === "data"){
							if ($row.cells[4].value==="НИЙТ ДҮН"){
								for (var v = 0; v < $row.cells.length; v++) {
									$row.cells[v]["background"]="#E0FFFF";
								}
							}
							if ($row.cells[4].value==="НИЙТ ДҮН БҮГД"){
								for (var v = 0; v < $row.cells.length; v++) {
									$row.cells[v]["background"]="#87CEFA";
								}
							}
						}
			            for (var j = 0; j < $row.cells.length; j++) {
			                var $cell = $row.cells[j];
							
			                $cell["borderTop"] = { color: "#000000" };
			                $cell["borderRight"] = { color: "##000000", };
			                $cell["borderBottom"] = { color: "#000000", };
			                $cell["borderLeft"] = { color: "#000000", };
			            }
						
			        }
		        e.workbook.sheets[0].rows.unshift(
		            {
		                cells: [
		                    {
		                        value: "",
		                       // background: "#7a7a7a",
		                        colSpan: 10,
		                        color: "##0d0d0d",
		                        rowSpan: 1
		                    }
		                ]
		            } )			
		        e.workbook.sheets[0].rows.unshift(
		            {
		                cells: [
		                    {
		                        value: "Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан",
		                       // background: "#7a7a7a",
		                        colSpan: 10,
		                        color: "##0d0d0d",
		                        rowSpan: 1,
								textAlign: "center",
								fontSize:20
		                    }
		                ]
		            } )
		        e.workbook.sheets[0].rows.unshift(
		            {
		                cells: [
		                    {
		                        value: "",
		                       // background: "#7a7a7a",
		                        colSpan: 10,
		                        color: "##0d0d0d",
		                        rowSpan: 1
		                    }
		                ]
		            } )
                },
			//custom excel
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
							Account: { type: "string" },
							Name: { type: "string" },
							Debit: { type: "number" },
							Credit: { type: "number" },
							C2: { type: "number" },
							CAccount: { type: "string" },
							Branch: { type: "string" },
						//	Istotal: { type: "boolean" }
						}
					}
				},
				pageSize: 4000
			},
//			rowTemplate: kendo.template($("#rowTemplate").html()),//өнгө оруулах
//			rowTemplate: rowTemplateString,
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
				{field: "Date", title: "Огноо",filterable: { multi: true },format: "{0: yyyy-MM-dd}" , width: "90px"},
				{field: "Number", title: "Дугаар",  width: "100px",filterable: { multi: true } /*filterable: {
                                cell: {
                                    operator: "contains",
                                    suggestionOperator: "contains"
                                }
                            }*/
				},
				{field: "Account", title: "Данс",filterable: { multi: true }},				
				{field: "Name", title: "Гүйлгээний утга",filterable: { multi: true }},
				{
				title: "Гүйлгээний дүн",
					columns: [
					{ field: "Debit", title:"Дебит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Debit, "n2")#', filterable: { multi: true, search: true}, width: "120px"},
					{ field: "Credit", title: "Кредит", attributes:{style:"text-align:right;"}, template: '#= kendo.toString(Credit, "n2")#',filterable: { multi: true }, width: "120px"},]
				},
				{field: "C2", title: "Үлдэгдэл",attributes:{style:"text-align:right;"}, template: '#= kendo.toString(C2, "n2")#',filterable: { multi: true },width: "120px"},				
				{field: "Account", title: "Харьцсан данс",filterable: { multi: true }},	
				{field: "Branch", title: "Салбар",filterable: { multi: true }},	
				//{field: "Istotal", title:"Дүн эсэх"}			
			],
			
			//Өнгө будах
		   dataBound: function(e) {
		            // get the index of the UnitsInStock cell
		            var columns = e.sender.columns;
		            var columnIndex = this.wrapper.find(".k-grid-header [data-field=" + "Name" + "]").index();
					var is_total=false;
					var is_init=false;
					var is_subtotal=false;

		            // iterate the data items and apply row styles where necessary
		            var dataItems = e.sender.dataSource.view();
		            for (var j = 0; j < dataItems.length; j++) {
		              var name = dataItems[j].get("Name");
		
						if (name=="НИЙТ ДҮН"){
							is_subtotal=true;
						}
						else{
							is_subtotal=false;
						}
						if (name=="НИЙТ ДҮН БҮГД"){
							is_total=true;
						}	
						else{
							is_total=false;
						}
						if (name=="Эхний үлдэгдэл"){
							is_init=true;
						}
						else{
							is_init=false;
						}		
		              var row = e.sender.tbody.find("[data-uid='" + dataItems[j].uid + "']");
  					  if (is_subtotal){
			                row.addClass("mw_subtotalcolor");
						}
  					  if (is_init){
			                row.addClass("mw_initcolor");
							}
			            }
		              if (is_total) {
		                row.addClass("mw_totaltcolor");
		              }
		          }			
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
        'mw_account_partner_detail_widget', AccountReportPartnerDetail
    );
	return AccountReportPartnerDetail;
});
