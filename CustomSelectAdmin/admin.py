"""
CustomSelectAdmin: A Trac plugin for modifying custom select fields
                   for tickets in a special admin panel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from trac.core import Component, implements, TracError
from trac.ticket import model
from trac.ticket.model import AbstractEnum
from trac.config import Option
from trac.util.translation import _
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider


class CustomSelectPanel(Component):
    implements(IAdminPanelProvider, ITemplateProvider)

    def _get_custom_fields(self):
        fields = []
        config = self.config['ticket-custom']
        for name in [option for option, value in config.options()
                     if '.' not in option]:
            panel = config.get(name + '.panel') or config.get(name + '.label')
            panel = panel or name.capitalize()
            field = {
                'name': name,
                'type': config.get(name),
                'order': config.getint(name + '.order', 0),
                'label': config.get(name + '.label') or name.capitalize(),
                'panel': panel}
            if field['type'] == 'select':
                field['options'] = config.getlist(name + '.options', sep='|')
                if '' in field['options']:
                    field['optional'] = True
                    field['options'].remove('')
                fields.append((field['name'], field['label'], field['panel']))
        return fields

    def _get_matching_field(self, page):
        for field in self._get_custom_fields():
            if field[2].replace(' ', '').lower() == page:
                return field

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            for field in self._get_custom_fields():
                yield ('ticket', 'Ticket System',
                       field[2].replace(' ', '').lower(),
                       field[2])

    def render_admin_panel(self, req, cat, page, path_info):
        fieldname, fieldlabel, fieldpanel = self._get_matching_field(page)
        self._type = page
        self._label = (fieldlabel, fieldpanel)
        req.perm.require('TICKET_ADMIN')
        data = {'label_singular': self._label[0],
                'label_plural': self._label[1]}
        optionstr = self.config.get('ticket-custom', fieldname + '.options')
        placeholder = optionstr.startswith('|')
        fieldoptions = optionstr.replace(' |', '|').replace('| ', '|')
        fieldoptions = fieldoptions.split('|')
        for option in fieldoptions:
            if option == '':
                fieldoptions.remove(option)
        default = self.config.get('ticket-custom', fieldname + '.value')
        if not default:
            if len(fieldoptions) > 0:
                default = fieldoptions[0]
            else:
                default = ''
        if req.method == 'POST':
            # Add enum
            if req.args.get('add') and req.args.get('name'):
                fieldoptions.append(req.args.get('name'))
            elif req.args.get('add'):
                raise TracError(_("No %s specified."))
            # Remove enums
            elif req.args.get('remove'):
                sel = req.args.get('sel')
                if not sel:
                    error_msg = 'No %s selected'
                    error_msg = error_msg % data['label_plural'].lower()
                    raise TracError(_(error_msg))
                if not isinstance(sel, list):
                    sel = [sel]
                for name in sel:
                    fieldoptions.remove(name)
            # Appy changes
            elif req.args.get('apply'):
                # Set default value
                if req.args.get('default'):
                    default = req.args.get('default')
                order = dict([(str(key[6:]),
                               str(int(req.args.get(key)))) for key
                              in req.args.keys()
                              if key.startswith('value_')])
                values = dict([(val, True) for val in order.values()])
                if len(order) != len(values):
                    raise TracError(_('Order numbers must be unique'))
                for value in order:
                    fieldoptions[int(order[value])] = value
            optionstr = '|'.join(fieldoptions)
            if req.args.get('blank_placeholder'):
                optionstr = '| ' + optionstr
                default = ''
                placeholder = True
            self.config.set('ticket-custom', fieldname + '.value', default)
            self.config.set('ticket-custom', fieldname + '.options', optionstr)
            self.config.save()
            req.redirect(req.href.admin(cat, page))
        data.update(dict(enums=fieldoptions,
                         default=default,
                         placeholder=placeholder,
                         view='list'))
        return 'custom_select_enums.html', data

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
