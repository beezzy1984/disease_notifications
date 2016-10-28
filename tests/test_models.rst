=======================

Carrier Weight Scenario

=======================


=============

General Setup

=============


Imports::


    >>> from datetime import datetime

    >>> from dateutil.relativedelta import relativedelta

    >>> from decimal import Decimal

    >>> from proteus import config, Model, Wizard

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase


Create database::

    >>> CONFIG = set_up_datebase(database_name='test_memory')

    >>> CONFIG.pool.test = True

Install health_disease_notification, health_disease_notification_history::


    >>> Module = Model.get('ir.module.module')

    >>> modules = Module.find([('name', 'in', [
    ...                         'health_disease_notification', 
    ...                         'health_disease_notification_history'
    ...                       ]),])

    >>> Module.install([x.id for x in modules], CONFIG.context)

    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')


Create Notification::


    >>> Patient = Model.get('gnuhealth.patient')

    >>> HealthProfessional = Model.get('gnuhealth.healthprofessional')

    >>> Notification = Model.get('gnuhealth.disease_notification')

    >>> patient, = Patient.find([('id', '=', '1')])

    >>> healthprof, = HealthProfessional.find([('id', '=', '1')])

    >>> Notification = Notification()

    >>> Notification.date_notified = datetime.now()

    >>> Notification.name = 'Code'

    >>> Notification.patient = patient

    >>> Notification.status = 'waiting'

    >>> Notification.healthprof = healthprof


Reload the context::


    >>> User = Model.get('res.user')

    >>> CONFIG._context = User.get_preferences(True, CONFIG.context)


Create fiscal year::


    >>> FiscalYear = Model.get('account.fiscalyear')

    >>> Sequence = Model.get('ir.sequence')

    >>> SequenceStrict = Model.get('ir.sequence.strict')

    >>> fiscalyear = FiscalYear(name='%s' % today.year)

    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)

    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)

    >>> fiscalyear.company = company

    >>> post_move_sequence = Sequence(name='%s' % today.year,

    ...     code='account.move',

    ...     company=company)

    >>> post_move_sequence.save()

    >>> fiscalyear.post_move_sequence = post_move_sequence

    >>> invoice_sequence = SequenceStrict(name='%s' % today.year,

    ...     code='account.invoice',

    ...     company=company)

    >>> invoice_sequence.save()

    >>> fiscalyear.out_invoice_sequence = invoice_sequence

    >>> fiscalyear.in_invoice_sequence = invoice_sequence

    >>> fiscalyear.out_credit_note_sequence = invoice_sequence

    >>> fiscalyear.in_credit_note_sequence = invoice_sequence

    >>> fiscalyear.save()

    >>> FiscalYear.create_period([fiscalyear.id], config.context)


Create chart of accounts::


    >>> AccountTemplate = Model.get('account.account.template')

    >>> Account = Model.get('account.account')

    >>> AccountJournal = Model.get('account.journal')

    >>> account_template, = AccountTemplate.find([('parent', '=', None)])

    >>> create_chart = Wizard('account.create_chart')

    >>> create_chart.execute('account')

    >>> create_chart.form.account_template = account_template

    >>> create_chart.form.company = company

    >>> create_chart.execute('create_account')

    >>> receivable, = Account.find([

    ...         ('kind', '=', 'receivable'),

    ...         ('company', '=', company.id),

    ...         ])

    >>> payable, = Account.find([

    ...         ('kind', '=', 'payable'),

    ...         ('company', '=', company.id),

    ...         ])

    >>> revenue, = Account.find([

    ...         ('kind', '=', 'revenue'),

    ...         ('company', '=', company.id),

    ...         ])

    >>> create_chart.form.account_receivable = receivable

    >>> create_chart.form.account_payable = payable

    >>> create_chart.execute('create_properties')


Create supplier::


    >>> Party = Model.get('party.party')

    >>> supplier = Party(name='Supplier')

    >>> supplier.save()


Create customer::


    >>> Party = Model.get('party.party')

    >>> customer = Party(name='Customer')

    >>> customer.save()


Create category::


    >>> ProductCategory = Model.get('product.category')

    >>> category = ProductCategory(name='Category')

    >>> category.save()


Create product::


    >>> ProductUom = Model.get('product.uom')

    >>> ProductTemplate = Model.get('product.template')

    >>> Product = Model.get('product.product')

    >>> unit, = ProductUom.find([('name', '=', 'Unit')])

    >>> gram, = ProductUom.find([('name', '=', 'Gram')])

    >>> product = Product()

    >>> template = ProductTemplate()

    >>> template.name = 'Product'

    >>> template.category = category

    >>> template.default_uom = unit

    >>> template.type = 'goods'

    >>> template.salable = True

    >>> template.list_price = Decimal('20')

    >>> template.cost_price = Decimal('8')

    >>> template.account_revenue = revenue

    >>> template.weight = 250

    >>> template.weight_uom = gram

    >>> template.save()

    >>> product.template = template

    >>> product.save()

    >>> carrier_product = Product()

    >>> carrier_template = ProductTemplate()

    >>> carrier_template.name = 'Carrier Product'

    >>> carrier_template.category = category

    >>> carrier_template.default_uom = unit

    >>> carrier_template.type = 'service'

    >>> carrier_template.salable = True

    >>> carrier_template.list_price = Decimal('3')

    >>> carrier_template.cost_price = Decimal('3')

    >>> carrier_template.account_revenue = revenue

    >>> carrier_template.save()

    >>> carrier_product.template = carrier_template

    >>> carrier_product.save()


Create carrier::


    >>> Carrier = Model.get('carrier')

    >>> WeightPriceList = Model.get('carrier.weight_price_list')

    >>> kilogram, = ProductUom.find([('name', '=', 'Kilogram')])

    >>> carrier = Carrier()

    >>> party = Party(name='Carrier')

    >>> party.save()

    >>> carrier.party = party

    >>> carrier.carrier_product = carrier_product

    >>> carrier.carrier_cost_method = 'weight'

    >>> carrier.weight_currency = currency

    >>> carrier.weight_uom = kilogram

    >>> for weight, price in (

    ...         (0.5, Decimal(25)),

    ...         (1, Decimal(40)),

    ...         (5, Decimal(180)),

    ...         ):

    ...     line = WeightPriceList(weight=weight, price=price)

    ...     carrier.weight_price_list.append(line)

    >>> carrier.save()


Receive a single product line::


    >>> ShipmentIn = Model.get('stock.shipment.in')

    >>> Move = Model.get('stock.move')

    >>> Location = Model.get('stock.location')

    >>> supplier_location, = Location.find([

    ...         ('code', '=', 'SUP'),

    ...         ])

    >>> shipment = ShipmentIn()

    >>> shipment.supplier = supplier

    >>> move = Move()

    >>> shipment.incoming_moves.append(move)

    >>> move.from_location = supplier_location

    >>> move.to_location = shipment.warehouse.input_location

    >>> move.product = product

    >>> move.quantity = 4

    >>> move.unit_price

    Decimal('8')

    >>> shipment.carrier = carrier

    >>> shipment.cost

    Decimal('25')

    >>> shipment.cost_currency == currency

    True

    >>> shipment.save()

    >>> ShipmentIn.receive([shipment.id], config.context)

    >>> shipment.reload()

    >>> shipment.state

    u'received'

    >>> move, = shipment.incoming_moves

    >>> move.unit_price

    Decimal('14.2500')


Create payment term::


    >>> PaymentTerm = Model.get('account.invoice.payment_term')

    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')

    >>> payment_term = PaymentTerm(name='Direct')

    >>> payment_term_line = PaymentTermLine(type='remainder', days=0)

    >>> payment_term.lines.append(payment_term_line)

    >>> payment_term.save()


Sale products with cost on shipment::


    >>> Sale = Model.get('sale.sale')

    >>> SaleLine = Model.get('sale.line')

    >>> sale = Sale()

    >>> sale.party = customer

    >>> sale.carrier = carrier

    >>> sale.payment_term = payment_term

    >>> sale.invoice_method = 'shipment'

    >>> sale.shipment_cost_method = 'shipment'

    >>> sale_line = SaleLine()

    >>> sale.lines.append(sale_line)

    >>> sale_line.product = product

    >>> sale_line.quantity = 5.0

    >>> cost_line = sale.lines[-1]

    >>> cost_line.product == carrier_product

    True

    >>> cost_line.quantity == 1

    True

    >>> cost_line.amount

    Decimal('40.00')

    >>> sale.save()

    >>> Sale.quote([sale.id], config.context)

    >>> Sale.confirm([sale.id], config.context)

    >>> Sale.process([sale.id], config.context)

    >>> sale.state

    u'processing'

    >>> sale.untaxed_amount

    Decimal('140.00')


Send products::


    >>> ShipmentOut = Model.get('stock.shipment.out')

    >>> shipment, = sale.shipments

    >>> shipment.carrier == carrier

    True

    >>> shipment.cost

    Decimal('40')

    >>> shipment.cost_currency == currency

    True

    >>> move, = shipment.inventory_moves

    >>> move.quantity = 4

    >>> shipment.cost

    Decimal('25')

    >>> shipment.cost_currency == currency

    True

    >>> shipment.state

    u'waiting'

    >>> shipment.save()

    >>> shipment.reload()

    >>> ShipmentOut.assign_force([shipment.id], config.context)

    >>> shipment.state

    u'assigned'

    >>> shipment.reload()

    >>> ShipmentOut.pack([shipment.id], config.context)

    >>> shipment.state

    u'packed'

    >>> shipment.reload()

    >>> ShipmentOut.done([shipment.id], config.context)

    >>> shipment.state

    u'done'


Check customer invoice::


    >>> sale.reload()

    >>> invoice, = sale.invoices

    >>> invoice.untaxed_amount

    Decimal('105.00')


Sale products with cost on order::


    >>> sale = Sale()

    >>> sale.party = customer

    >>> sale.carrier = carrier

    >>> sale.payment_term = payment_term

    >>> sale.invoice_method = 'order'

    >>> sale.shipment_cost_method = 'order'

    >>> sale_line = SaleLine()

    >>> sale.lines.append(sale_line)

    >>> sale_line.product = product

    >>> sale_line.quantity = 3.0

    >>> cost_line = sale.lines[-1]

    >>> cost_line.product == carrier_product

    True

    >>> cost_line.quantity == 1

    True

    >>> cost_line.amount

    Decimal('25.00')

    >>> sale.save()

    >>> Sale.quote([sale.id], config.context)

    >>> Sale.confirm([sale.id], config.context)

    >>> Sale.process([sale.id], config.context)

    >>> sale.state

    u'processing'

    >>> sale.untaxed_amount

    Decimal('85.00')


Check customer shipment::


    >>> shipment, = sale.shipments

    >>> shipment.carrier == carrier

    True


Check customer invoice::


    >>> sale.reload()

    >>> invoice, = sale.invoices

    >>> invoice.untaxed_amount

    Decimal('85.00')