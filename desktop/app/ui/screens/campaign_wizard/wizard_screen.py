from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from app.engine.call_engine import CallEngine
from app.engine.campaign_engine import CampaignEngine
from app.repositories import campaigns_repo, contacts_repo, devices_repo, messages_repo
from app.services.message import render
from app.ui.screens.campaign_wizard.step_compose import StepCompose
from app.ui.screens.campaign_wizard.step_confirm import StepConfirm
from app.ui.screens.campaign_wizard.step_import import StepImport
from app.ui.screens.campaign_wizard.step_preview import StepPreview
from app.ui.screens.campaign_wizard.step_select import StepSelect
from app.ui.screens.campaign_wizard.step_send_monitor import StepSendMonitor
from app.ui.screens.campaign_wizard.step_validate import StepValidate


class CampaignWizardScreen(QWidget):
    """Controller for import -> validate -> select -> compose -> preview -> confirm -> send.

    When campaign_type is CALL the compose and preview steps are skipped
    (there is no SMS body to write).
    """

    def __init__(self, network_client=None, parent=None):
        super().__init__(parent)
        self.network_client = network_client
        self.engine = CampaignEngine(network_client, self) if network_client else None
        self.call_engine = CallEngine(network_client, self) if network_client else None
        self._connected = False
        self._selected_contact_ids: list[str] = []
        self._message_body: str = ""
        self._campaign_type: str = "SMS"  # "SMS" or "CALL"

        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.step_import = StepImport()
        self.step_validate = StepValidate()
        self.step_select = StepSelect()
        self.step_compose = StepCompose()
        self.step_preview = StepPreview()
        self.step_confirm = StepConfirm()

        # Send monitor supports both engines
        active_engine = self.engine or self.call_engine
        self.step_send_monitor = StepSendMonitor(active_engine, self.call_engine) if active_engine else None

        for step in (
            self.step_import, self.step_validate, self.step_select,
            self.step_compose, self.step_preview, self.step_confirm,
        ):
            self.stack.addWidget(step)
        if self.step_send_monitor:
            self.stack.addWidget(self.step_send_monitor)

        self.step_import.imported.connect(self._on_imported)
        self.step_validate.continued.connect(self._on_validated)
        self.step_select.continued.connect(self._on_selected)
        self.step_compose.continued.connect(self._on_composed)
        self.step_preview.continued.connect(self._on_previewed)
        self.step_confirm.start_sending.connect(self._on_start_sending)

        if self.network_client:
            self.network_client.connected.connect(self._on_client_connected)
            self.network_client.disconnected.connect(self._on_client_disconnected)

    def set_campaign_type(self, campaign_type: str) -> None:
        """Called from the confirm step or externally to set the campaign mode."""
        self._campaign_type = campaign_type

    def _on_client_connected(self) -> None:
        self._connected = True

    def _on_client_disconnected(self, _reason: str) -> None:
        self._connected = False

    # -- step transitions --------------------------------------------------
    def _on_imported(self, result) -> None:
        self.step_validate.load_result(result)
        self.stack.setCurrentWidget(self.step_validate)

    def _on_validated(self) -> None:
        self.step_select.reload()
        self.stack.setCurrentWidget(self.step_select)

    def _on_selected(self, contact_ids: list[str]) -> None:
        self._selected_contact_ids = contact_ids
        if self._campaign_type == "CALL":
            # Skip compose/preview for call campaigns — go straight to confirm
            paired = devices_repo.list_all(paired_only=True)
            device_id = paired[0]["id"] if paired else None
            self.step_confirm.load(
                len(self._selected_contact_ids), "",
                device_id, self._connected, campaign_type="CALL",
            )
            self.stack.setCurrentWidget(self.step_confirm)
        else:
            self.step_compose.reload_templates()
            self.stack.setCurrentWidget(self.step_compose)

    def _on_composed(self, message_body: str) -> None:
        self._message_body = message_body
        self.step_preview.load(self._selected_contact_ids, message_body)
        self.stack.setCurrentWidget(self.step_preview)

    def _on_previewed(self) -> None:
        paired = devices_repo.list_all(paired_only=True)
        device_id = paired[0]["id"] if paired else None
        self.step_confirm.load(
            len(self._selected_contact_ids), self._message_body,
            device_id, self._connected, campaign_type="SMS",
        )
        self.stack.setCurrentWidget(self.step_confirm)

    def _on_start_sending(
        self,
        rate_limit_ms: int,
        daily_limit: int,
        campaign_type: str = "SMS",
        ring_duration_sec: int = 15,
        audio_path: str = "",
    ) -> None:
        import base64
        import os

        self._campaign_type = campaign_type
        paired = devices_repo.list_all(paired_only=True)
        device_id = paired[0]["id"] if paired else None

        is_call = campaign_type == "CALL"
        msg_body = "" if is_call else self._message_body

        campaign_id = campaigns_repo.create(
            name=f"{'Call' if is_call else 'SMS'} Campaign {len(campaigns_repo.list_all()) + 1}",
            message_body=msg_body,
            campaign_type=campaign_type,
            device_id=device_id,
            rate_limit_ms=rate_limit_ms,
            daily_limit=daily_limit,
            ring_duration_sec=ring_duration_sec,
            audio_path=audio_path if (is_call and audio_path) else None,
        )

        # Upload audio to phone before dispatch if audio is present
        if is_call and audio_path and os.path.exists(audio_path) and self.network_client:
            try:
                with open(audio_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("ascii")
                self.network_client.send_upload_call_audio(
                    campaign_id=campaign_id,
                    filename=os.path.basename(audio_path),
                    audio_base64=b64_data,
                )
            except Exception:
                pass

        for contact_id in self._selected_contact_ids:
            contact = contacts_repo.get(contact_id)
            if contact is None:
                continue
            if is_call:
                rendered = f"[CALL] {contact['name']}"
            else:
                rendered = render(self._message_body, contact["name"])
            messages_repo.create(campaign_id, contact_id, contact["phone_e164"], rendered)
        campaigns_repo.refresh_counts(campaign_id)

        if self.step_send_monitor:
            self.stack.setCurrentWidget(self.step_send_monitor)
            if is_call and self.call_engine:
                self.step_send_monitor.start(campaign_id, is_call=True)
            else:
                self.step_send_monitor.start(campaign_id, is_call=False)

    def reset(self, campaign_type: str = "SMS") -> None:
        """Call to start a fresh 'New Campaign' or 'Voice Call' flow."""
        self._selected_contact_ids = []
        self._message_body = ""
        self._campaign_type = campaign_type
        self.stack.setCurrentWidget(self.step_import)
