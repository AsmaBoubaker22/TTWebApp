from flask.views import MethodView
from flask_smorest import Blueprint
from flask import request, jsonify
from .models import db, User, UsageHistory, Balance, Recharge, MonetaryRechargePlan, MobileDataPlan, AgencyLocation, Question, Answer
from datetime import datetime

apiblp = Blueprint('users', __name__, description="Operations on Users")

# Convert date string to datetime.date object
def convert_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None


# endpoints for Users simulated data------------------------------------------------------------------------------------------
@apiblp.route('/api/users')
class Users(MethodView):
    def get(self):
        """Get all users."""
        users = User.query.all()
        return [
            {
                "id": user.id,
                "phoneNumber": user.phoneNumber,
                "username": user.username,
                "bonusPlan": user.bonusPlan
            }
            for user in users
        ], 200

    def post(self):
     """Add one or more users with provided JSON data."""
     data = request.get_json()

     if not isinstance(data, list):
        data = [data]  # Wrap single object in a list

     created_users = []
     for user_data in data:
        # Check for required fields
        if not user_data or "phoneNumber" not in user_data or "bonusPlan" not in user_data:
            return jsonify({"error": "Each user must have phoneNumber and bonusPlan fields."}), 400

        # Check if user already exists
        if User.query.filter_by(phoneNumber=user_data["phoneNumber"]).first():
            return jsonify({"error": f"User with phone number {user_data['phoneNumber']} already exists."}), 400

        # Add user to database
        user = User(
            phoneNumber=user_data["phoneNumber"],
            username=user_data.get("username"),
            passwordHash=None,
            bonusPlan=user_data["bonusPlan"]
        )
        db.session.add(user)
        created_users.append({"bonsPlan": user.bonusPlan, "phoneNumber": user.phoneNumber})

     db.session.commit()
     return jsonify({"message": "Users added successfully.", "users": created_users}), 201

    def delete(self):
        """Delete all users."""
        num_deleted = db.session.query(User).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} users."}), 200


@apiblp.route('/api/users/<int:user_id>')
class SingleUser(MethodView):
    def get(self, user_id):
        """Retrieve a user by ID."""
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        return {
            "id": user.id,
            "phoneNumber": user.phoneNumber,
            "username": user.username,
            "bonusPlan": user.bonusPlan
        }, 200

    def delete(self, user_id):
        """Delete a user by ID."""
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User with ID {user_id} deleted."}), 200


# endpoints for Users history simulated data------------------------------------------------------------------------------------------
@apiblp.route('/api/usageHistory')
class UsageHistoryAPI(MethodView):
    def get(self):
        """Get all usage history records."""
        usage_history = UsageHistory.query.all()
        return [
            {
                "id": entry.id,
                "userId": entry.userId,
                "usageTimestamp": entry.usageTimestamp,
                "callsMinutes": entry.callsMinutes,
                "smsCount": entry.smsCount,
                "dataUsageMB": entry.dataUsageMB
            }
            for entry in usage_history
        ], 200

    def post(self):
        """Add one or more usage history records."""
        data = request.get_json()

        if not isinstance(data, list):
            data = [data]  # Wrap single object in a list

        created_entries = []
        for entry_data in data:
            # Check for required fields
            if not entry_data or "userId" not in entry_data:
                return jsonify({"error": "Each entry must have userId."}), 400

            # Ensure at least one usage field is provided
            if not any(
                field in entry_data
                for field in ["callsMinutes", "smsCount", "dataUsageMB"]
            ):
                return jsonify(
                    {"error": "At least one field (callsMinutes, smsCount, or dataUsageMB) must be provided."}
                ), 400
            
            # Convert usageTimestamp to datetime
            try:
                entry_data["usageTimestamp"] = datetime.fromisoformat(entry_data["usageTimestamp"])
            except ValueError:
                return jsonify({"error": f"Invalid datetime format for usageTimestamp: {entry_data['usageTimestamp']}"}), 400

            # Add usage entry to database
            usage_entry = UsageHistory(
                userId=entry_data["userId"],
                usageTimestamp=entry_data.get("usageTimestamp"),
                callsMinutes=entry_data.get("callsMinutes", 0),
                smsCount=entry_data.get("smsCount", 0),
                dataUsageMB=entry_data.get("dataUsageMB", 0.0),
            )
            db.session.add(usage_entry)
            created_entries.append(
                {
                    "userId": usage_entry.userId,
                    "usageTimestamp": usage_entry.usageTimestamp,
                    "callsMinutes": usage_entry.callsMinutes,
                    "smsCount": usage_entry.smsCount,
                    "dataUsageMB": usage_entry.dataUsageMB,
                }
            )

        db.session.commit()
        return jsonify({"message": "Usage history added successfully.", "usage": created_entries}), 201

    def delete(self):
        """Delete all usage history records."""
        num_deleted = db.session.query(UsageHistory).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} usage history records."}), 200


@apiblp.route('/api/usageHistory/<int:usage_id>')
class SingleUsageHistory(MethodView):
    def get(self, usage_id):
        """Retrieve a usage history record by ID."""
        entry = UsageHistory.query.get(usage_id)
        if not entry:
            return jsonify({"error": "Usage history not found."}), 404

        return {
            "id": entry.id,
            "userId": entry.userId,
            "usageTimestamp": entry.usageTimestamp,
            "callsMinutes": entry.callsMinutes,
            "smsCount": entry.smsCount,
            "dataUsageMB": entry.dataUsageMB
        }, 200

    def delete(self, usage_id):
        """Delete a usage history record by ID."""
        entry = UsageHistory.query.get(usage_id)
        if not entry:
            return jsonify({"error": "Usage history not found."}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": f"Usage history with ID {usage_id} deleted."}), 200


@apiblp.route('/api/usageHistory/user/<int:user_id>', methods=['GET'])
def usageHistoryByUser(user_id):
    """Get usage history for a specific user."""
    usage_records = UsageHistory.query.filter_by(userId=user_id).all()
    if not usage_records:
        return jsonify({"message": "No usage history found for this user."}), 404
    
    result = [
        {
            "userId": record.userId,
            "usageTimestamp": record.usageTimestamp.isoformat(),
            "callsMinutes": record.callsMinutes,
            "smsCount": record.smsCount,
            "dataUsageMB": record.dataUsageMB
        }
        for record in usage_records
    ]
    return jsonify(result), 200


# endpoints for Balancee simulated data------------------------------------------------------------------------------------------
@apiblp.route('/api/balances')
class Balances(MethodView):
    def get(self):
        """Get all balances."""
        balances = Balance.query.all()
        return [
            {
                "id": balance.id,
                "userId": balance.userId,
                "monetaryBalance": balance.monetaryBalance,
                "bonusBalance": balance.bonusBalance,
                "dataBalanceMB": balance.dataBalanceMB,
                "monetaryExpiryDate": balance.monetaryExpiryDate.isoformat() if balance.monetaryExpiryDate else None,
                "bonusExpiryDate": balance.bonusExpiryDate.isoformat() if balance.bonusExpiryDate else None,
                "dataExpiryDate": balance.dataExpiryDate.isoformat() if balance.dataExpiryDate else None,
            }
            for balance in balances
        ], 200

    
    def post(self):
        """Add one or more balances."""
        data = request.get_json()

        if not isinstance(data, list):
            data = [data]  # Wrap single object in a list

        created_balances = []
        for balance_data in data:
            # Check for required fields
            if "userId" not in balance_data:
                return jsonify({"error": "Each balance must have a userId field."}), 400

            # Check if balance for user already exists
            if Balance.query.filter_by(userId=balance_data["userId"]).first():
                return jsonify({"error": f"Balance for user ID {balance_data['userId']} already exists."}), 400

            # Set missing data to 0 if not provided
            monetaryBalance = balance_data.get("monetaryBalance", 0)
            bonusBalance = balance_data.get("bonusBalance", 0)
            dataBalanceMB = balance_data.get("dataBalanceMB", 0)

            # Set expiry dates to None if the corresponding balance is 0
            monetaryExpiryDate = balance_data.get("monetaryExpiryDate") if monetaryBalance > 0 else None
            bonusExpiryDate = balance_data.get("bonusExpiryDate") if bonusBalance > 0 else None
            dataExpiryDate = balance_data.get("dataExpiryDate") if dataBalanceMB > 0 else None

             # Convert dates to Python datetime.date objects if they are not None
            if monetaryExpiryDate:
                monetaryExpiryDate = convert_date(monetaryExpiryDate)
            if bonusExpiryDate:
                bonusExpiryDate = convert_date(bonusExpiryDate)
            if dataExpiryDate:
                dataExpiryDate = convert_date(dataExpiryDate)

            # Add balance to the database
            balance = Balance(
                userId=balance_data["userId"],
                monetaryBalance=monetaryBalance,
                bonusBalance=bonusBalance,
                dataBalanceMB=dataBalanceMB,
                monetaryExpiryDate=monetaryExpiryDate,
                bonusExpiryDate=bonusExpiryDate,
                dataExpiryDate=dataExpiryDate,
            )
            db.session.add(balance)
            created_balances.append({
                "userId": balance.userId,
                "monetaryBalance": balance.monetaryBalance,
                "bonusBalance": balance.bonusBalance,
                "dataBalanceMB": balance.dataBalanceMB,
            })

        db.session.commit()
        return jsonify({"message": "Balances added successfully.", "balances": created_balances}), 201

    def delete(self):
        """Delete all balances."""
        num_deleted = db.session.query(Balance).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} balances."}), 200


@apiblp.route('/api/balances/<int:balance_id>')
class SingleBalance(MethodView):
    def get(self, balance_id):
        """Retrieve a balance by ID."""
        balance = Balance.query.get(balance_id)
        if not balance:
            return jsonify({"error": "Balance not found."}), 404

        return {
            "id": balance.id,
            "userId": balance.userId,
            "monetaryBalance": balance.monetaryBalance,
            "bonusBalance": balance.bonusBalance,
            "dataBalanceMB": balance.dataBalanceMB,
            "monetaryExpiryDate": balance.monetaryExpiryDate.isoformat() if balance.monetaryExpiryDate else None,
            "bonusExpiryDate": balance.bonusExpiryDate.isoformat() if balance.bonusExpiryDate else None,
            "dataExpiryDate": balance.dataExpiryDate.isoformat() if balance.dataExpiryDate else None,
        }, 200

    def delete(self, balance_id):
        """Delete a balance by ID."""
        balance = Balance.query.get(balance_id)
        if not balance:
            return jsonify({"error": "Balance not found."}), 404

        db.session.delete(balance)
        db.session.commit()
        return jsonify({"message": f"Balance with ID {balance_id} deleted."}), 200


@apiblp.route('/api/balances/user/<int:user_id>', methods=['GET', 'PATCH', 'DELETE'])
class BalanceByUserId(MethodView):
    def get(self, user_id):
        """Retrieve the balance by user ID."""
        balance = Balance.query.filter_by(userId=user_id).first()
        if not balance:
            return jsonify({"error": "Balance not found for user."}), 404

        return jsonify({
            "userId": balance.userId,
            "monetaryBalance": balance.monetaryBalance,
            "bonusBalance": balance.bonusBalance,
            "dataBalanceMB": balance.dataBalanceMB,
            "monetaryExpiryDate": balance.monetaryExpiryDate.isoformat() if balance.monetaryExpiryDate else None,
            "bonusExpiryDate": balance.bonusExpiryDate.isoformat() if balance.bonusExpiryDate else None,
            "dataExpiryDate": balance.dataExpiryDate.isoformat() if balance.dataExpiryDate else None,
        }), 200

    def patch(self, user_id):
        """Partially update the balance for a user by their ID."""
        balance = Balance.query.filter_by(userId=user_id).first()
        if not balance:
            return jsonify({"error": "Balance not found for user."}), 404

        data = request.get_json()

         # Convert dates to Python datetime.date objects if they are not None
        if "monetaryExpiryDate" in data and data["monetaryExpiryDate"]:
            data["monetaryExpiryDate"] = convert_date(data["monetaryExpiryDate"])
        if "bonusExpiryDate" in data and data["bonusExpiryDate"]:
            data["bonusExpiryDate"] = convert_date(data["bonusExpiryDate"])
        if "dataExpiryDate" in data and data["dataExpiryDate"]:
            data["dataExpiryDate"] = convert_date(data["dataExpiryDate"])

        # Update fields if provided in the request
        if "monetaryBalance" in data:
            balance.monetaryBalance = data["monetaryBalance"]
        if "bonusBalance" in data:
            balance.bonusBalance = data["bonusBalance"]
        if "dataBalanceMB" in data:
            balance.dataBalanceMB = data["dataBalanceMB"]
        if "monetaryExpiryDate" in data:
            balance.monetaryExpiryDate = data["monetaryExpiryDate"]
        if "bonusExpiryDate" in data:
            balance.bonusExpiryDate = data["bonusExpiryDate"]
        if "dataExpiryDate" in data:
            balance.dataExpiryDate = data["dataExpiryDate"]

        db.session.commit()

        return jsonify({
            "userId": balance.userId,
            "monetaryBalance": balance.monetaryBalance,
            "bonusBalance": balance.bonusBalance,
            "dataBalanceMB": balance.dataBalanceMB,
            "monetaryExpiryDate": balance.monetaryExpiryDate.isoformat() if balance.monetaryExpiryDate else None,
            "bonusExpiryDate": balance.bonusExpiryDate.isoformat() if balance.bonusExpiryDate else None,
            "dataExpiryDate": balance.dataExpiryDate.isoformat() if balance.dataExpiryDate else None,
        }), 200


# endpoints for recharge history simulated data------------------------------------------------------------------------------------------
@apiblp.route('/api/recharges')
class Recharges(MethodView):
    def get(self):
        """Retrieve all recharges."""
        recharges = Recharge.query.all()
        return [
            {
                "id": recharge.id,
                "userId": recharge.userId,
                "rechargeAmount": recharge.rechargeAmount,
                "rechargeDate": recharge.rechargeDate.isoformat() if recharge.rechargeDate else None,
                "bonusAdded": recharge.bonusAdded,
                "dataAddedMB": recharge.dataAddedMB,
                "monetaryExpiryDate": recharge.monetaryExpiryDate.isoformat() if recharge.monetaryExpiryDate else None,
                "bonusExpiryDate": recharge.bonusExpiryDate.isoformat() if recharge.bonusExpiryDate else None,
                "dataExpiryDate": recharge.dataExpiryDate.isoformat() if recharge.dataExpiryDate else None,
            }
            for recharge in recharges
        ], 200

    def post(self):
        """Add one or more recharges."""
        data = request.get_json()

        if not isinstance(data, list):
            data = [data]  # Wrap single object in a list

        created_recharges = []
        for recharge_data in data:
            if "userId" not in recharge_data:
                return jsonify({"error": "Each recharge must have a userId field."}), 400

            rechargeAmount = recharge_data.get("rechargeAmount", 0)
            bonusAdded = recharge_data.get("bonusAdded", 0)
            dataAddedMB = recharge_data.get("dataAddedMB", 0)

            # Constraint: Either money and bonus or mobile data must be provided
            if (rechargeAmount > 0 or bonusAdded > 0) and dataAddedMB > 0:
                return jsonify({"error": "Cannot provide both monetary/bonus and data recharge together."}), 400
            if rechargeAmount == 0 and bonusAdded == 0 and dataAddedMB == 0:
                return jsonify({"error": "At least one of rechargeAmount, bonusAdded, or dataAddedMB must be provided."}), 400

            # Set expiry dates to None if no balance is provided
            monetaryExpiryDate = recharge_data.get("monetaryExpiryDate") if rechargeAmount > 0 else None
            bonusExpiryDate = recharge_data.get("bonusExpiryDate") if bonusAdded > 0 else None
            dataExpiryDate = recharge_data.get("dataExpiryDate") if dataAddedMB > 0 else None

            # Convert dates to Python datetime.date objects if they are not None
            if monetaryExpiryDate:
                monetaryExpiryDate = convert_date(monetaryExpiryDate)
            if bonusExpiryDate:
                bonusExpiryDate = convert_date(bonusExpiryDate)
            if dataExpiryDate:
                dataExpiryDate = convert_date(dataExpiryDate)

            # Convert and use a specific recharge date if provided
            rechargeDate = recharge_data.get("rechargeDate")
            if rechargeDate:
                rechargeDate = convert_date(rechargeDate)

            recharge = Recharge(
                userId=recharge_data["userId"],
                rechargeAmount=rechargeAmount,
                rechargeDate=rechargeDate,  # Use the provided or default date
                bonusAdded=bonusAdded,
                dataAddedMB=dataAddedMB,
                monetaryExpiryDate=monetaryExpiryDate,
                bonusExpiryDate=bonusExpiryDate,
                dataExpiryDate=dataExpiryDate,
            )
            db.session.add(recharge)
            created_recharges.append({
                "userId": recharge.userId,
                "rechargeAmount": recharge.rechargeAmount,
                "bonusAdded": recharge.bonusAdded,
                "dataAddedMB": recharge.dataAddedMB,
            })

        db.session.commit()
        return jsonify({"message": "Recharges added successfully.", "recharges": created_recharges}), 201


    def delete(self):
        """Delete all recharges."""
        num_deleted = db.session.query(Recharge).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} recharges."}), 200


@apiblp.route('/api/recharges/<int:recharge_id>')
class SingleRecharge(MethodView):
    def get(self, recharge_id):
        """Retrieve a recharge by ID."""
        recharge = Recharge.query.get(recharge_id)
        if not recharge:
            return jsonify({"error": "Recharge not found."}), 404

        return {
            "id": recharge.id,
            "userId": recharge.userId,
            "rechargeAmount": recharge.rechargeAmount,
            "rechargeDate": recharge.rechargeDate.isoformat() if recharge.rechargeDate else None,
            "bonusAdded": recharge.bonusAdded,
            "dataAddedMB": recharge.dataAddedMB,
            "monetaryExpiryDate": recharge.monetaryExpiryDate.isoformat() if recharge.monetaryExpiryDate else None,
            "bonusExpiryDate": recharge.bonusExpiryDate.isoformat() if recharge.bonusExpiryDate else None,
            "dataExpiryDate": recharge.dataExpiryDate.isoformat() if recharge.dataExpiryDate else None,
        }, 200

    def delete(self, recharge_id):
        """Delete a recharge by ID."""
        recharge = Recharge.query.get(recharge_id)
        if not recharge:
            return jsonify({"error": "Recharge not found."}), 404

        db.session.delete(recharge)
        db.session.commit()
        return jsonify({"message": f"Recharge with ID {recharge_id} deleted."}), 200


@apiblp.route('/api/recharges/user/<int:user_id>')
class UserRecharges(MethodView):
    def get(self, user_id):
        """Retrieve all recharges for a user by their ID."""
        recharges = Recharge.query.filter_by(userId=user_id).all()
        if not recharges:
            return jsonify({"error": f"No recharges found for user with ID {user_id}."}), 404

        return [
            {
                "id": recharge.id,
                "userId": recharge.userId,
                "rechargeAmount": recharge.rechargeAmount,
                "rechargeDate": recharge.rechargeDate.isoformat() if recharge.rechargeDate else None,
                "bonusAdded": recharge.bonusAdded,
                "dataAddedMB": recharge.dataAddedMB,
                "monetaryExpiryDate": recharge.monetaryExpiryDate.isoformat() if recharge.monetaryExpiryDate else None,
                "bonusExpiryDate": recharge.bonusExpiryDate.isoformat() if recharge.bonusExpiryDate else None,
                "dataExpiryDate": recharge.dataExpiryDate.isoformat() if recharge.dataExpiryDate else None,
            }
            for recharge in recharges
        ], 200


# endpoints for monetary recharge plans simulated data------------------------------------------------------------------------------------------
@apiblp.route('/api/monetaryPlans')
class MonetaryRechargePlans(MethodView):
    def get(self):
        """Retrieve all recharge plans."""
        plans = MonetaryRechargePlan.query.all()
        return [
            {
                "id": plan.id,
                "price": plan.price,
                "rechargeAmount": plan.rechargeAmount,
                "rechargeExpDays": plan.rechargeExpDays,
                "bonusExpDays": plan.bonusExpDays,
            }
            for plan in plans
        ], 200

    def post(self):
        """Add one or more recharge plans."""
        data = request.get_json()

        if not isinstance(data, list):
            data = [data]  # Wrap single object in a list

        created_plans = []
        for plan_data in data:
            if "price" not in plan_data or "rechargeAmount" not in plan_data or "rechargeExpDays" not in plan_data or "bonusExpDays" not in plan_data:
                return jsonify({"error": "Each plan must have price, rechargeAmount, rechargeExpDays, and bonusExpDays fields."}), 400

            plan = MonetaryRechargePlan(
                price=plan_data["price"],
                rechargeAmount=plan_data["rechargeAmount"],
                rechargeExpDays=plan_data["rechargeExpDays"],
                bonusExpDays=plan_data["bonusExpDays"]
            )
            db.session.add(plan)
            created_plans.append({
                "id": plan.id,
                "price": plan.price,
                "rechargeAmount": plan.rechargeAmount,
                "rechargeExpDays": plan.rechargeExpDays,
                "bonusExpDays": plan.bonusExpDays,
            })

        db.session.commit()
        return jsonify({"message": "Plans added successfully.", "plans": created_plans}), 201


    def delete(self):
        """Delete all recharge plans."""
        num_deleted = db.session.query(MonetaryRechargePlan).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} recharge plans."}), 200


@apiblp.route('/api/monetaryPlans/<int:plan_id>')
class SingleMonetaryRechargePlan(MethodView):
    def get(self, plan_id):
        """Retrieve a recharge plan by ID."""
        plan = MonetaryRechargePlan.query.get(plan_id)
        if not plan:
            return jsonify({"error": "Plan not found."}), 404

        return {
            "id": plan.id,
            "price": plan.price,
            "rechargeAmount": plan.rechargeAmount,
            "rechargeExpDays": plan.rechargeExpDays,
            "bonusExpDays": plan.bonusExpDays,
        }, 200

    def delete(self, plan_id):
        """Delete a recharge plan by ID."""
        plan = MonetaryRechargePlan.query.get(plan_id)
        if not plan:
            return jsonify({"error": "Plan not found."}), 404

        db.session.delete(plan)
        db.session.commit()
        return jsonify({"message": f"Plan with ID {plan_id} deleted."}), 200


# endpoints for mobile data plans simulated data-----------------------------------------------------------------------------------------
@apiblp.route('/api/mobileDataPlans')
class MobileDataPlans(MethodView):
    def get(self):
        """Retrieve all mobile data plans."""
        plans = MobileDataPlan.query.all()
        return [
            {
                "id": plan.id,
                "price": plan.price,
                "dataAmountMB": plan.dataAmountMB,
                "expDays": plan.expDays,
            }
            for plan in plans
        ], 200

    def post(self):
        """Add one or more mobile data plans."""
        data = request.get_json()

        if not isinstance(data, list):
            data = [data]  # Wrap single object in a list

        created_plans = []
        for plan_data in data:
            if "price" not in plan_data or "dataAmountMB" not in plan_data or "expDays" not in plan_data:
                return jsonify({"error": "Each plan must have price, dataAmountMB, and expDays fields."}), 400

            plan = MobileDataPlan(
                price=plan_data["price"],
                dataAmountMB=plan_data["dataAmountMB"],
                expDays=plan_data["expDays"]
            )
            db.session.add(plan)
            created_plans.append({
                "price": plan.price,
                "dataAmountMB": plan.dataAmountMB,
                "expDays": plan.expDays,
            })

        db.session.commit()
        return jsonify({"message": "Mobile data plans added successfully.", "plans": created_plans}), 201


    def delete(self):
        """Delete all mobile data plans."""
        num_deleted = db.session.query(MobileDataPlan).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} mobile data plans."}), 200


@apiblp.route('/api/mobileDataPlans/<int:plan_id>')
class SingleMobileDataPlan(MethodView):
    def get(self, plan_id):
        """Retrieve a mobile data plan by ID."""
        plan = MobileDataPlan.query.get(plan_id)
        if not plan:
            return jsonify({"error": "Plan not found."}), 404

        return {
            "id": plan.id,
            "price": plan.price,
            "dataAmountMB": plan.dataAmountMB,
            "expDays": plan.expDays,
        }, 200

    def delete(self, plan_id):
        """Delete a mobile data plan by ID."""
        plan = MobileDataPlan.query.get(plan_id)
        if not plan:
            return jsonify({"error": "Plan not found."}), 404

        db.session.delete(plan)
        db.session.commit()
        return jsonify({"message": f"Plan with ID {plan_id} deleted."}), 200


# endpoints for agencies location ------------------------------------------------------------------------------------------
@apiblp.route('/api/agencyLocations')
class AgencyLocations(MethodView):
    def get(self):
        """Retrieve all agency locations."""
        agency_locations = AgencyLocation.query.all()
        return [
            {
                "id": agency.id,
                "name": agency.name,
                "address": agency.address,
                "phoneNumber": agency.phoneNumber,
                "latitude": agency.latitude,
                "longitude": agency.longitude,
            }
            for agency in agency_locations
        ], 200

    def post(self):
        """Add one or more agency locations."""
        data = request.get_json()

        if not isinstance(data, list):
            data = [data]  # Wrap single object in a list

        created_agencies = []
        for agency_data in data:
            if "name" not in agency_data or "address" not in agency_data or "phoneNumber" not in agency_data or "latitude" not in agency_data or "longitude" not in agency_data:
                return jsonify({"error": "Each agency location must have name, address, phoneNumber, latitude, and longitude fields."}), 400

            agency = AgencyLocation(
                name=agency_data["name"],
                address=agency_data["address"],
                phoneNumber=agency_data["phoneNumber"],
                latitude=agency_data["latitude"],
                longitude=agency_data["longitude"]
            )
            db.session.add(agency)
            created_agencies.append({
                "id": agency.id,
                "name": agency.name,
                "address": agency.address,
                "phoneNumber": agency.phoneNumber,
                "latitude": agency.latitude,
                "longitude": agency.longitude,
            })

        db.session.commit()
        return jsonify({"message": "Agency locations added successfully.", "locations": created_agencies}), 201

    def delete(self):
        """Delete all agency locations."""
        num_deleted = db.session.query(AgencyLocation).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} agency locations."}), 200


@apiblp.route('/api/agencyLocations/<int:location_id>')
class SingleAgencyLocation(MethodView):
    def get(self, location_id):
        """Retrieve an agency location by ID."""
        agency = AgencyLocation.query.get(location_id)
        if not agency:
            return jsonify({"error": "Agency location not found."}), 404

        return {
            "id": agency.id,
            "name": agency.name,
            "address": agency.address,
            "phoneNumber": agency.phoneNumber,
            "latitude": agency.latitude,
            "longitude": agency.longitude,
        }, 200

    def delete(self, location_id):
        """Delete an agency location by ID."""
        agency = AgencyLocation.query.get(location_id)
        if not agency:
            return jsonify({"error": "Agency location not found."}), 404

        db.session.delete(agency)
        db.session.commit()
        return jsonify({"message": f"Agency location with ID {location_id} deleted."}), 200


# these endpoints are only to check the data available manipulated by the users in the client-side api------------------------------------------------------------------------------------------
# checking questions------------------------------------------------------------------------------------------
@apiblp.route('/api/questions')
class QuestionsCheck(MethodView):
    def get(self):
        """Retrieve all questions."""
        questions = Question.query.all()
        return [
            {
                "id": question.id,
                "userId": question.userId,
                "content": question.content,
                "submittedAt": question.submittedAt.isoformat()  # Format datetime to string
            }
            for question in questions
        ], 200

    def delete(self):
        """Delete all questions."""
        num_deleted = db.session.query(Question).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} questions."}), 200

@apiblp.route('/api/questions/user/<int:user_id>')
class UserQuestions(MethodView):
    def get(self, user_id):
        """Retrieve all questions submitted by a specific user."""
        questions = Question.query.filter_by(userId=user_id).all()
        if not questions:
            return jsonify({"message": f"No questions found for user ID {user_id}."}), 404

        return [
            {
                "id": question.id,
                "userId": question.userId,
                "content": question.content,
                "submittedAt": question.submittedAt.isoformat()
            }
            for question in questions
        ], 200

@apiblp.route('/api/questions/<int:question_id>', methods=['DELETE'])
class DeleteQuestion(MethodView):
    def delete(self, question_id):
        """Delete a specific question."""
        question = Question.query.get(question_id)
        if not question:
            return jsonify({"error": "Question not found."}), 404

        db.session.delete(question)
        db.session.commit()
        return jsonify({"message": "Question deleted successfully."}), 200


# checking answers------------------------------------------------------------------------------------------
@apiblp.route('/api/answers')
class AnswersCheck(MethodView):
    def get(self):
        """Retrieve all answers."""
        answers = Answer.query.all()
        return [
            {
                "id": answer.id,
                "questionId": answer.questionId,
                "userId": answer.userId,
                "content": answer.content,
                "submittedAt": answer.submittedAt.isoformat()  # Format datetime to string
            }
            for answer in answers
        ], 200

    def delete(self):
        """Delete all answers."""
        num_deleted = db.session.query(Answer).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} answers."}), 200


@apiblp.route('/api/answers/question/<int:question_id>')
class QuestionAnswers(MethodView):
    def get(self, question_id):
        """Retrieve all answers for a specific question."""
        answers = Answer.query.filter_by(questionId=question_id).all()
        if not answers:
            return jsonify({"message": f"No answers found for question ID {question_id}."}), 404

        return [
            {
                "id": answer.id,
                "questionId": answer.questionId,
                "userId": answer.userId,
                "content": answer.content,
                "submittedAt": answer.submittedAt.isoformat()
            }
            for answer in answers
        ], 200

@apiblp.route('/api/answers/user/<int:user_id>')
class UserAnswers(MethodView):
    def get(self, user_id):
        """Retrieve all answers submitted by a specific user."""
        answers = Answer.query.filter_by(userId=user_id).all()
        if not answers:
            return jsonify({"message": f"No answers found for user ID {user_id}."}), 404

        return [
            {
                "id": answer.id,
                "questionId": answer.questionId,
                "userId": answer.userId,
                "content": answer.content,
                "submittedAt": answer.submittedAt.isoformat()
            }
            for answer in answers
        ], 200

