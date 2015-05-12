# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CrossedSelection
                                 A QGIS plugin
 This plugin helps to select features in a layer according to values from a field of another layer
                             -------------------
        begin                : 2014-09-26
        copyright            : (C) 2014 by Harrissou SANT-ANNA
        email                : delazj@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load CrossedSelection class from file CrossedSelection.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .crossed_selection import CrossedSelection
    return CrossedSelection(iface)
