(function () {
  "use strict";

  var embed = document.querySelector(".prd-embed");
  if (!embed) return;

  function qs(sel, root) {
    return (root || embed).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || embed).querySelectorAll(sel));
  }

  window.PRDKIT = window.PRDKIT || {};

  window.PRDKIT.switchProtoTab = function (tabId) {
    if (!tabId) return;
    qsa('.proto-tab[data-tab="' + tabId + '"]').forEach(function (btn) {
      var on = btn.getAttribute("data-tab") === tabId;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    qsa(".proto-page").forEach(function (page) {
      var on = page.getAttribute("data-proto-page") === tabId;
      page.classList.toggle("is-active", on);
      page.hidden = !on;
    });
    qsa("#pay-sub a").forEach(function (a) {
      a.classList.toggle("is-active", a.getAttribute("data-nav") === tabId);
    });
  };

  function setModal(name, show) {
    qsa('[data-modal="' + name + '"]').forEach(function (el) {
      el.hidden = !show;
    });
  }

  function setDrawer(name, show) {
    qsa('[data-drawer="' + name + '"]').forEach(function (el) {
      el.hidden = !show;
      if (show) el.classList.add("is-open");
      else el.classList.remove("is-open");
    });
  }

  function showToast(msg) {
    var toast = qs(".proto-toast");
    if (!toast) return;
    toast.textContent = msg || "操作成功";
    toast.classList.add("is-show");
    setTimeout(function () {
      toast.classList.remove("is-show");
    }, 2200);
  }

  function initPaySidebar() {
    var payItem = null;
    qsa(".sidebar-menu .menu-item").forEach(function (el) {
      var lbl = el.querySelector(".menu-label");
      if (lbl && lbl.textContent.trim() === "支付管理") payItem = el;
    });
    if (!payItem || qs("#pay-sub")) return;
    payItem.setAttribute("href", "javascript:void(0)");
    payItem.classList.add("is-pay-active");
    var subEl = document.createElement("div");
    subEl.className = "sidebar-sub is-show";
    subEl.id = "pay-sub";
    subEl.innerHTML =
      '<a href="javascript:void(0)" data-nav="bill" class="is-active">账单管理</a>' +
      '<a href="javascript:void(0)" data-nav="audit">平账审核</a>';
    payItem.insertAdjacentElement("afterend", subEl);
    payItem.addEventListener("click", function (e) {
      e.preventDefault();
      subEl.classList.toggle("is-show");
    });
    subEl.addEventListener("click", function (e) {
      var link = e.target.closest("[data-nav]");
      if (!link) return;
      e.preventDefault();
      window.PRDKIT.switchProtoTab(link.getAttribute("data-nav"));
    });
  }

  function updBatch() {
    var batch = qs('[data-batch-bar]');
    if (!batch) return;
    var n = qsa(".row-chk:checked").length;
    batch.hidden = n === 0;
  }

  embed.addEventListener("click", function (e) {
    var t = e.target;
    var tabBtn = t.closest(".proto-tab");
    if (tabBtn) {
      window.PRDKIT.switchProtoTab(tabBtn.getAttribute("data-tab"));
      return;
    }
    var segTab = t.closest(".proto-seg-tab");
    if (segTab) {
      var segBar = segTab.closest(".proto-seg-tabs");
      if (segBar) {
        qsa(".proto-seg-tab", segBar).forEach(function (b) {
          b.classList.toggle("is-active", b === segTab);
        });
      }
      return;
    }
    var pill = t.closest(".proto-pill");
    if (pill) {
      var pillBar = pill.closest(".proto-pill-tabs");
      if (pillBar) {
        qsa(".proto-pill", pillBar).forEach(function (b) {
          b.classList.toggle("is-active", b === pill);
        });
      }
      return;
    }
    var stratItem = t.closest(".proto-strategy-item");
    if (stratItem) {
      var list = stratItem.closest(".proto-strategy-list");
      if (list) {
        qsa(".proto-strategy-item", list).forEach(function (li) {
          li.classList.toggle("is-active", li === stratItem);
        });
      }
      return;
    }
    var toggleF = t.closest("[data-toggle-filter]");
    if (toggleF) {
      e.preventDefault();
      var qf = toggleF.closest(".query-form");
      if (qf) {
        qf.classList.toggle("is-filter-expanded");
        toggleF.textContent = qf.classList.contains("is-filter-expanded") ? "收起" : "展开";
      }
      return;
    }
    var openM = t.closest("[data-open-modal]");
    if (openM) {
      e.preventDefault();
      var modalName = openM.getAttribute("data-open-modal");
      if (modalName === "pass-batch") {
        var n = qsa(".row-chk:checked").length;
        var msg = qs("#batch-pass-msg");
        if (msg) msg.textContent = "是否要批量通过这 " + n + " 笔申请？";
      }
      setModal(modalName, true);
      return;
    }
    var closeM = t.closest("[data-close-modal]");
    if (closeM) {
      setModal(closeM.getAttribute("data-close-modal"), false);
      var toastMsg = closeM.getAttribute("data-toast");
      if (toastMsg) showToast(toastMsg);
      return;
    }
    var openD = t.closest("[data-open-drawer]");
    if (openD) {
      setDrawer(openD.getAttribute("data-open-drawer"), true);
      return;
    }
    var closeD = t.closest("[data-close-drawer]");
    if (closeD) {
      setDrawer(closeD.getAttribute("data-close-drawer"), false);
      return;
    }
    var dBack = t.closest(".proto-drawer-backdrop");
    if (dBack && t === dBack) {
      setDrawer(dBack.getAttribute("data-drawer"), false);
      return;
    }
    if (t.closest(".proto-modal-backdrop") && t.classList.contains("proto-modal-backdrop")) {
      setModal(t.getAttribute("data-modal"), false);
      return;
    }
    var chip = t.closest(".proto-chip");
    if (chip) {
      var ta = qs("#reject-reason");
      if (ta) ta.value = chip.getAttribute("data-t") || "";
      return;
    }
    if (t.closest("[data-voucher-remove]")) {
      e.preventDefault();
      e.stopPropagation();
      var vItem = t.closest("[data-voucher-item]");
      if (vItem) vItem.remove();
      syncApplyVoucherUi();
      return;
    }
    if (t.closest("[data-voucher-upload]")) {
      e.preventDefault();
      addMockVoucherThumb();
      return;
    }
    if (t.closest("[data-voucher-preview]")) {
      setModal("lightbox", true);
      return;
    }
    var more = t.closest(".proto-more");
    if (more && t.closest(".proto-more > .btn-link")) {
      qsa(".proto-more.is-open").forEach(function (x) {
        if (x !== more) x.classList.remove("is-open");
      });
      more.classList.toggle("is-open");
      return;
    }
    if (t.hasAttribute("data-lb-prev") || t.hasAttribute("data-lb-next")) {
      return;
    }
  });

  document.addEventListener("click", function (e) {
    if (!e.target.closest(".proto-more")) {
      qsa(".proto-more.is-open").forEach(function (x) {
        x.classList.remove("is-open");
      });
    }
  });

  embed.addEventListener("change", function (e) {
    if (e.target.id === "chk-all") {
      var on = e.target.checked;
      qsa(".row-chk:not(:disabled)").forEach(function (c) {
        c.checked = on;
      });
      updBatch();
    }
    if (e.target.classList.contains("row-chk")) updBatch();
  });

  qsa(".proto-tabs").forEach(function (bar) {
    bar.addEventListener("click", function (e) {
      var btn = e.target.closest(".proto-tab");
      if (btn) window.PRDKIT.switchProtoTab(btn.getAttribute("data-tab"));
    });
  });

  var sidebar = embed.querySelector("#sidebar");
  var toggleBtn = embed.querySelector("#btn-toggle-sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("is-collapsed");
    });
  }

  document.querySelectorAll(".toc-tree a[data-proto-tab]").forEach(function (a) {
    a.addEventListener("click", function () {
      var tab = a.getAttribute("data-proto-tab");
      if (tab) window.PRDKIT.switchProtoTab(tab);
    });
  });

  function syncApplyVoucherUi() {
    var list = qs("#apply-voucher-thumbs");
    var zone = qs("[data-voucher-upload]");
    if (!list || !zone) return;
    var n = list.querySelectorAll("[data-voucher-item]").length;
    zone.classList.toggle("is-hidden", n >= 3);
  }

  function addMockVoucherThumb() {
    var list = qs("#apply-voucher-thumbs");
    if (!list || list.querySelectorAll("[data-voucher-item]").length >= 3) return;
    var wrap = document.createElement("div");
    wrap.className = "proto-vthumb-item";
    wrap.setAttribute("data-voucher-item", "");
    wrap.innerHTML =
      '<span class="proto-vthumb" data-voucher-preview aria-label="付款凭证"><svg class="proto-vthumb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M3 16l5-5 4 4 5-6 4 5"/></svg></span>' +
      '<button type="button" class="proto-vthumb-remove" data-voucher-remove aria-label="删除凭证">×</button>';
    list.appendChild(wrap);
    syncApplyVoucherUi();
  }

  function closeAllOverlays() {
    qsa("[data-modal]").forEach(function (el) {
      el.hidden = true;
    });
    qsa("[data-drawer]").forEach(function (el) {
      el.hidden = true;
      el.classList.remove("is-open");
    });
    qsa(".proto-more.is-open").forEach(function (el) {
      el.classList.remove("is-open");
    });
  }

  function initMoreMenus() {
    qsa(".proto-more").forEach(function (more) {
      var closeTimer;
      more.addEventListener("mouseenter", function () {
        clearTimeout(closeTimer);
        qsa(".proto-more.is-open").forEach(function (x) {
          if (x !== more) x.classList.remove("is-open");
        });
        more.classList.add("is-open");
      });
      more.addEventListener("mouseleave", function () {
        closeTimer = setTimeout(function () {
          more.classList.remove("is-open");
        }, 200);
      });
    });
  }

  function initFilterCollapse() {
    qsa(".query-form").forEach(function (form) {
      var wrap = form.querySelector(".filter-collapse-wrap");
      if (!wrap) return;
      var hasExtra = form.querySelector(".filter-item--extra");
      if (!hasExtra) {
        wrap.hidden = true;
        return;
      }
      wrap.hidden = false;
      var btn = wrap.querySelector("[data-toggle-filter]");
      if (btn) {
        btn.textContent = form.classList.contains("is-filter-expanded") ? "收起" : "展开";
      }
    });
  }

  initPaySidebar();
  initMoreMenus();
  initFilterCollapse();
  closeAllOverlays();
  var firstTab = qs(".proto-tab.is-active") || qs(".proto-tab");
  syncApplyVoucherUi();
  if (firstTab) window.PRDKIT.switchProtoTab(firstTab.getAttribute("data-tab"));
})();
