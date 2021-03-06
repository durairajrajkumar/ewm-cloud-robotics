**
** Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
**
** This file is part of ewm-cloud-robotics
** (see https://github.com/SAP/ewm-cloud-robotics).
**
** This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
**
function zconfirm_warehouse_task.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(IV_LGNUM) TYPE  /SCWM/LGNUM
*"     REFERENCE(IV_TANUM) TYPE  /SCWM/TANUM
*"     REFERENCE(IV_NISTA) TYPE  /SCWM/LTAP_NISTA
*"     REFERENCE(IV_ALTME) TYPE  /SCWM/DE_AUNIT
*"     REFERENCE(IV_NLPLA) TYPE  /SCWM/LTAP_NLPLA
*"     REFERENCE(IV_NLENR) TYPE  /SCWM/DE_DESHU
*"     REFERENCE(IV_PARTI) TYPE  /SCWM/LTAP_CONF_PARTI
*"     REFERENCE(IV_CONF_EXC) TYPE  CHAR4
*"  EXPORTING
*"     REFERENCE(ET_LTAP_VB) TYPE  /SCWM/TT_LTAP_VB
*"  EXCEPTIONS
*"      WHT_NOT_CONFIRMED
*"      WHT_ALREADY_CONFIRMED
*"----------------------------------------------------------------------

  data: lv_severity type bapi_mtype,
        ls_to_conf  type /scwm/to_conf,
        lt_bapiret  type bapirettab,
        lt_ltap_vb  type /scwm/tt_ltap_vb,
        lt_to_conf  type /scwm/to_conf_tt,
        ls_conf_exc	type /scwm/s_conf_exc,
        lt_conf_exc	type /scwm/tt_conf_exc.

* Prepare input parameter for Warehouse Task confirmation
  ls_to_conf-tanum = iv_tanum.
  ls_to_conf-nista = iv_nista.
  ls_to_conf-altme = iv_altme.
  ls_to_conf-nlpla = iv_nlpla.
  ls_to_conf-nlenr = iv_nlenr.
  ls_to_conf-parti = iv_parti.

  append ls_to_conf to lt_to_conf.

* Prepare Exception Code table if parameter was set
  if iv_conf_exc is not initial.
    ls_conf_exc-exccode = iv_conf_exc.
    ls_conf_exc-tanum = iv_tanum.
    ls_conf_exc-papos = 0.
    ls_conf_exc-buscon = wmegc_buscon_tim.
    ls_conf_exc-exec_step = wmegc_execstep_04.
    append ls_conf_exc to lt_conf_exc.
  endif.


* Confirm Warehouse Task
  call function '/SCWM/TO_CONFIRM'
    exporting
      iv_lgnum       = iv_lgnum
      iv_wtcode      = wmegc_wtcode_rsrc
      iv_update_task = abap_false
      iv_commit_work = abap_false
      it_conf        = lt_to_conf
      it_conf_exc    = lt_conf_exc
    importing
      et_ltap_vb     = lt_ltap_vb
      et_bapiret     = lt_bapiret
      ev_severity    = lv_severity.

* commit work and wait to ensure next OData calls is getting actual data
  commit work and wait.

* Check for errors
  if lv_severity ca 'EA'.
    read table lt_bapiret with key type = 'E'
                                   id = '/SCWM/L3'
                                   number = 022
                                   transporting no fields.
    if sy-subrc = 0.
      raise wht_already_confirmed.
    else.
      raise wht_not_confirmed.
    endif.
  else.
    et_ltap_vb = lt_ltap_vb.
  endif.

endfunction.
