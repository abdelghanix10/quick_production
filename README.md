# Quick Production (Odoo 20)

**Quick Production** (`quick_production`) provides a streamlined, touchscreen-friendly "Kiosk Mode" interface for manufacturing and production staff to quickly register, queue, and complete production orders in **Odoo 20**.

---

## Features

### 1. Visual Kiosk Dashboard
- **Kanban Product Cards**: Displays product images, names, current **On-Hand Stock**, and **Unit of Measure (UoM)**.
- **Role & Multi-Category Filtering**:
  - **System Administrators**: View and produce all products across the database.
  - **Production Staff**: View only products belonging to their assigned **Primary Production Category** and/or **Additional Production Categories** (including child categories).

### 2. Quick Production Wizard
- **Touchscreen Quantity Keypad**: Increment production quantities effortlessly on tablets or kiosks using **`+1`**, **`+5`**, **`+10`**, **`+50`**, and **`Reset (1)`** buttons.
- **Real-Time BOM & Stock Availability Check**:
  - Automatically explodes the product's active Bill of Materials (BOM) based on the requested batch quantity.
  - Displays each ingredient's **Required Qty** alongside its current **On-Hand Qty**.
  - Highlights ingredient shortages with a **Stock Status** badge (`Available` vs `Shortage`) and a top-level warning banner.
- **Dual Production Modes**:
  - **Produce Immediately (Done)**: Creates the Manufacturing Order (MO), confirms it, consumes components, and marks it as **Done** in a single click.
  - **Queue Production (Pending)**: Creates and confirms the MO so it is added to the **Produce All** pending queue for later completion.

### 3. Bulk Pending Production ("Produce All")
- **Multi-User Safe**: Scoped per active user so multiple operators can manage their pending queues simultaneously without conflict.
- **One-Click "Fill Planned Quantities"**: Automatically populates the quantity to produce with the planned quantity across selected lines.
- **Partial Production & Backorders**: Producing less than the planned quantity automatically handles component scaling and creates a backorder for the remainder.
- **Edit Planned Quantity Wizard**: Adjust the planned MO quantity on the fly and automatically recalculate required component quantities.
- **Single-Row & Batch Completion**: Complete individual orders (`check`) or batch-complete selected orders (`Produce Selected`), or cancel orders (`close`).

### 4. Today's Orders Tracking
- Dedicated **Today's Orders** menu item to monitor all Manufacturing Orders created during the current day.

---

## Configuration

### User Setup
To configure which product categories a user can view and produce:

1. Go to **Settings → Users & Companies → Users**.
2. Open the user profile you wish to configure.
3. Open the **Quick Production** tab.
4. Configure one or both fields:
   - **Primary Production Category**: The main product category for the operator (e.g., *Bakery*, *Pastry*, *Kitchen*).
   - **Additional Production Categories**: Any extra product categories the operator is allowed to produce.
   - *Note: Non-admin users without any assigned category will see an empty dashboard.*

---

## Usage

1. **Open the App**: Click **Quick Production** from the main Odoo app switcher.
2. **Select a Product**: Tap any product card on the **Dashboard**.
3. **Set Quantity & Review Ingredients**:
   - Enter the quantity manually or use the **`+1` / `+5` / `+10` / `+50`** keypad buttons.
   - Review the **Ingredients Required** tab and check for any `Shortage` badges.
4. **Register Production**:
   - Click **Produce Immediately (Done)** to complete the production right away.
   - Click **Queue Production (Pending)** to start the order and finish it later from **Produce All**.
5. **Complete Queued Orders**:
   - Navigate to **Quick Production → Produce All**.
   - Adjust quantities if needed (or click **Fill Planned Quantities**), then click **Done** on individual rows or **Produce Selected** in the header.

---

## Technical Details

- **Odoo Version**: `20.0.2.0.0`
- **Technical Name**: `quick_production`
- **Dependencies**: `mrp`, `stock`, `product`
- **Odoo 20 Architecture**:
  - Uses Odoo 20's unified `security/ir.access.csv` access control model.
  - Uses Odoo 20 Material Symbols ligature icons (`edit`, `check`, `close`).
  - Uses `fields.Command` ORM syntax.
- **Models**:
  - `res.users` (extended with `production_category_id` and `production_category_ids`)
  - `product.product` (extended with `action_open_quick_production_wizard`)
  - `quick.production.wizard` & `quick.production.wizard.line` (`TransientModel`)
  - `quick.production.list` (`TransientModel`)
  - `quick.production.edit.wizard` & `quick.production.edit.wizard.line` (`TransientModel`)

---

## Installation

1. Place the `quick_production` folder inside your Odoo 20 `addons` directory.
2. Restart the Odoo server.
3. Activate **Developer Mode**, go to **Apps → Update Apps List**.
4. Search for **Quick Production** and click **Activate**.

---

## License

LGPL-3